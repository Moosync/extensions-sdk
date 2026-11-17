package api

import (
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"strconv"
	"strings"
	"time"

	pdk "github.com/extism/go-pdk"
	pdkhttp "github.com/extism/go-pdk/http"
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/types/known/durationpb"

	extensions "github.com/moosync/moosync/types/extensions"
	songs "github.com/moosync/moosync/types/songs"
)

var extension any

func RegisterExtension(ext any) {
	extension = ext
}

//go:wasmimport extism:host/user send_main_command
func send_main_command(uint64) uint64

func DispatchMainCommand(cmd *extensions.MainCommand) (*extensions.MainCommandResponse, error) {
	cmdBytes, err := proto.Marshal(cmd)
	if err != nil {
		return nil, err
	}

	mem := pdk.AllocateBytes(cmdBytes)
	ptr := send_main_command(mem.Offset())
	resMem := pdk.FindMemory(ptr)

	res := &extensions.MainCommandResponse{}
	if err := proto.Unmarshal(resMem.ReadBytes(), res); err != nil {
		return nil, err
	}

	if errResp, ok := res.Response.(*extensions.MainCommandResponse_Error); ok {
		return nil, fmt.Errorf("Host error: %s", errResp.Error.Message)
	}

	return res, nil
}




func parseLrcTimestamp(tag string) (int64, bool) {
	parts := strings.Split(tag, ":")
	if len(parts) != 2 {
		return 0, false
	}
	min, err := strconv.ParseInt(parts[0], 10, 64)
	if err != nil {
		return 0, false
	}
	secParts := strings.Split(parts[1], ".")
	sec, err := strconv.ParseInt(secParts[0], 10, 64)
	if err != nil {
		return 0, false
	}
	var millis int64 = 0
	if len(secParts) > 1 {
		frac := secParts[1]
		val, err := strconv.ParseInt(frac, 10, 64)
		if err == nil {
			switch len(frac) {
			case 1:
				millis = val * 100
			case 2:
				millis = val * 10
			case 3:
				millis = val
			default:
				millis, _ = strconv.ParseInt(frac[:3], 10, 64)
			}
		}
	}
	return min*60000 + sec*1000 + millis, true
}

func ParseLrc(lrcText string) (*songs.Lyrics, error) {
	trimmed := strings.TrimSpace(lrcText)
	if len(trimmed) == 0 {
		return nil, errors.New("empty LRC text")
	}

	var lines []*songs.LyricLine
	hasTimestamps := false

	rawLines := strings.Split(trimmed, "\n")
	for _, rawLine := range rawLines {
		line := strings.TrimSpace(rawLine)
		if len(line) == 0 {
			continue
		}

		remaining := line
		var timestamps []int64

		for strings.HasPrefix(remaining, "[") {
			closeIdx := strings.Index(remaining, "]")
			if closeIdx == -1 {
				break
			}
			tag := remaining[1:closeIdx]
			if ms, ok := parseLrcTimestamp(tag); ok {
				timestamps = append(timestamps, ms)
				remaining = remaining[closeIdx+1:]
			} else if strings.Contains(tag, ":") && (len(tag) == 0 || tag[0] < '0' || tag[0] > '9') {
				remaining = remaining[closeIdx+1:]
			} else {
				break
			}
		}

		text := strings.TrimSpace(remaining)
		if len(timestamps) > 0 {
			hasTimestamps = true
			for _, ms := range timestamps {
				lines = append(lines, &songs.LyricLine{
					Text:   text,
					TimeMs: ms,
				})
			}
		} else if !hasTimestamps && len(text) > 0 {
			lines = append(lines, &songs.LyricLine{
				Text:   text,
				TimeMs: 0,
			})
		}
	}

	return &songs.Lyrics{
		Lines:    lines,
		IsSynced: hasTimestamps,
	}, nil
}

func LogTrace(format string, args ...any) {
	pdk.Log(pdk.LogTrace, fmt.Sprintf(format, args...))
}

func LogDebug(format string, args ...any) {
	pdk.Log(pdk.LogDebug, fmt.Sprintf(format, args...))
}

func LogInfo(format string, args ...any) {
	pdk.Log(pdk.LogInfo, fmt.Sprintf(format, args...))
}

func LogWarn(format string, args ...any) {
	pdk.Log(pdk.LogWarn, fmt.Sprintf(format, args...))
}

func LogError(format string, args ...any) {
	pdk.Log(pdk.LogError, fmt.Sprintf(format, args...))
}

func EnableHttp() {
	http.DefaultTransport = &pdkhttp.HTTPTransport{}
}

func init() {
	// Force export of handle_extension_command to prevent dead code elimination
	_ = handle_extension_command
}

// DurationToProto converts a native time.Duration to a protobuf duration.
func DurationToProto(d time.Duration) *durationpb.Duration {
	return durationpb.New(d)
}

// ProtoToDuration converts a protobuf duration to a native time.Duration.
func ProtoToDuration(d *durationpb.Duration) time.Duration {
	if d == nil {
		return 0
	}
	return d.AsDuration()
}

type PlaybackDetailsReturnType struct {
	Duration      time.Duration
	Url           string
	DecryptionKey string
}

type HttpRequest struct {
	URL       string
	Method    string
	Headers   map[string]string
	Body      []byte
	TimeoutMs uint64
}

type HttpResponse struct {
	StatusCode uint32
	StatusText string
	Headers    map[string]string
	Body       []byte
}

func (r *HttpResponse) OK() bool {
	return r.StatusCode >= 200 && r.StatusCode < 300
}

func (r *HttpResponse) Text() string {
	return string(r.Body)
}

func (r *HttpResponse) JSON(v any) error {
	return json.Unmarshal(r.Body, v)
}

func BatchHttpRequestList(requests []HttpRequest) ([]HttpResponse, []error) {
	if len(requests) == 0 {
		return nil, nil
	}

	protoReqs := make([]*extensions.HttpRequest, len(requests))
	for i, r := range requests {
		method := r.Method
		if method == "" {
			method = "GET"
		}
		var timeout *uint64
		if r.TimeoutMs > 0 {
			timeout = &r.TimeoutMs
		}
		protoReqs[i] = &extensions.HttpRequest{
			Url:       r.URL,
			Method:    method,
			Headers:   r.Headers,
			Body:      r.Body,
			TimeoutMs: timeout,
		}
	}

	batch := &extensions.BatchHttpRequest{
		Requests: protoReqs,
	}

	respBatch, err := HostBatchHttpRequest(batch)
	if err != nil {
		return nil, []error{err}
	}

	if respBatch.Error != nil && *respBatch.Error != "" {
		return nil, []error{errors.New(*respBatch.Error)}
	}

	responses := make([]HttpResponse, 0, len(respBatch.Responses))
	var errs []error
	for i, res := range respBatch.Responses {
		switch r := res.Result.(type) {
		case *extensions.HttpResult_Response:
			if r.Response != nil {
				responses = append(responses, HttpResponse{
					StatusCode: r.Response.StatusCode,
					StatusText: r.Response.StatusText,
					Headers:    r.Response.Headers,
					Body:       r.Response.Body,
				})
			}
		case *extensions.HttpResult_Error:
			errs = append(errs, fmt.Errorf("request #%d failed: %s", i, r.Error))
		default:
			errs = append(errs, fmt.Errorf("request #%d returned empty result", i))
		}
	}

	if len(errs) > 0 {
		return responses, errs
	}
	return responses, nil
}

func BatchHttpGet(urls []string, headers map[string]string) ([]HttpResponse, []error) {
	reqs := make([]HttpRequest, len(urls))
	for i, u := range urls {
		reqs[i] = HttpRequest{
			URL:     u,
			Method:  "GET",
			Headers: headers,
		}
	}
	return BatchHttpRequestList(reqs)
}

func DoHttpRequest(req HttpRequest) (HttpResponse, error) {
	resps, errs := BatchHttpRequestList([]HttpRequest{req})
	if len(errs) > 0 {
		return HttpResponse{}, errs[0]
	}
	if len(resps) == 0 {
		return HttpResponse{}, errors.New("host runner returned empty response")
	}
	return resps[0], nil
}

func HttpGet(url string, headers map[string]string) (HttpResponse, error) {
	return DoHttpRequest(HttpRequest{
		URL:     url,
		Method:  "GET",
		Headers: headers,
	})
}

type ChildProcess struct {
	ID  uint64
	PID uint32
}

func (c *ChildProcess) WriteStdin(data []byte) (uint64, error) {
	resp, err := WriteProcessStdin(&extensions.WriteProcessStdinRequest{
		ProcessId: c.ID,
		Data:      data,
	})
	if err != nil {
		return 0, err
	}
	return resp.BytesWritten, nil
}

func (c *ChildProcess) ReadStdout(maxBytes uint64) ([]byte, error) {
	var max *uint64
	if maxBytes > 0 {
		max = &maxBytes
	}
	resp, err := ReadProcessStdout(&extensions.ReadProcessStdoutRequest{
		ProcessId: c.ID,
		MaxBytes:  max,
	})
	if err != nil {
		return nil, err
	}
	return resp.Data, nil
}

func (c *ChildProcess) ReadStdoutString(maxBytes uint64) (string, error) {
	bytes, err := c.ReadStdout(maxBytes)
	if err != nil {
		return "", err
	}
	return string(bytes), nil
}

func (c *ChildProcess) Kill() (bool, error) {
	resp, err := KillProcess(&extensions.KillProcessRequest{
		ProcessId: c.ID,
	})
	if err != nil {
		return false, err
	}
	return resp.Success, nil
}

func (c *ChildProcess) GetStatus() (bool, *int32, error) {
	resp, err := GetProcessStatus(&extensions.GetProcessStatusRequest{
		ProcessId: c.ID,
	})
	if err != nil {
		return false, nil, err
	}
	return resp.IsRunning, resp.ExitCode, nil
}

func SpawnProcess(path string, args []string, env map[string]string) (*ChildProcess, error) {
	resp, err := HostSpawnProcess(&extensions.SpawnProcessRequest{
		Path: path,
		Args: args,
		Env:  env,
	})
	if err != nil {
		return nil, err
	}
	return &ChildProcess{
		ID:  resp.ProcessId,
		PID: resp.Pid,
	}, nil
}


