package api

import (
	"sync"

	extensions "github.com/moosync/moosync/types/extensions"
)

type processHandlers struct {
	onStdout func([]byte)
	onStderr func([]byte)
	onExit   func(int32)
}

var (
	processHandlersMu   sync.Mutex
	processHandlersMap  = make(map[uint64]*processHandlers)
	defaultChildProcess = &ChildProcess{}
)

func updateProcessHandler(id uint64, fn func(*processHandlers)) {
	processHandlersMu.Lock()
	defer processHandlersMu.Unlock()
	entry, ok := processHandlersMap[id]
	if !ok {
		entry = &processHandlers{}
		processHandlersMap[id] = entry
	}
	fn(entry)
}

func (p *ChildProcess) OnStdout(cb func([]byte)) {
	updateProcessHandler(p.ID, func(entry *processHandlers) {
		entry.onStdout = cb
	})
}

func (p *ChildProcess) OnStderr(cb func([]byte)) {
	updateProcessHandler(p.ID, func(entry *processHandlers) {
		entry.onStderr = cb
	})
}

func (p *ChildProcess) OnExit(cb func(int32)) {
	updateProcessHandler(p.ID, func(entry *processHandlers) {
		entry.onExit = cb
	})
}

func (p *ChildProcess) Remove() {
	processHandlersMu.Lock()
	defer processHandlersMu.Unlock()
	delete(processHandlersMap, p.ID)
}

func (*ChildProcess) handleEvent(req *extensions.ProcessEventRequest) {
	if req == nil {
		return
	}
	switch ev := req.Event.(type) {
	case *extensions.ProcessEventRequest_Output:
		if ev.Output == nil {
			return
		}
		processHandlersMu.Lock()
		var onStdout func([]byte)
		var onStderr func([]byte)
		if entry, ok := processHandlersMap[req.ProcessId]; ok {
			onStdout = entry.onStdout
			onStderr = entry.onStderr
		}
		processHandlersMu.Unlock()
		if len(ev.Output.Stdout) > 0 && onStdout != nil {
			onStdout(ev.Output.Stdout)
		}
		if len(ev.Output.Stderr) > 0 && onStderr != nil {
			onStderr(ev.Output.Stderr)
		}
	case *extensions.ProcessEventRequest_Exited:
		processHandlersMu.Lock()
		var cb func(int32)
		if entry, ok := processHandlersMap[req.ProcessId]; ok {
			cb = entry.onExit
			delete(processHandlersMap, req.ProcessId)
		}
		processHandlersMu.Unlock()
		if cb != nil {
			cb(ev.Exited)
		}
	}
}
