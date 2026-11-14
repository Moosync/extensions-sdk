package api

import (
	pdk "github.com/extism/go-pdk"
)

type PlatformInfo struct {
	OS   string
	Arch string
}

func GetPlatform() PlatformInfo {
	osVal, ok := pdk.GetConfig("os")
	if !ok || osVal == "" {
		osVal = "unknown"
	}
	archVal, ok := pdk.GetConfig("arch")
	if !ok || archVal == "" {
		archVal = "unknown"
	}
	return PlatformInfo{
		OS:   osVal,
		Arch: archVal,
	}
}
