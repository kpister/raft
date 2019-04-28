package main

import (
	"github.com/kpister/raft/raft"
)

func min(a, b int32) int32 {
	if a < b {
		return a
	}
	return b
}

func max(a, b int32) int32 {
	if a > b {
		return a
	}
	return b
}

func isEqual(e1 *raft.Entry, e2 *raft.Entry) bool {
	if e1.Term == e2.Term {
		return true
	}
	return false
}

func resizeSlice(a []*raft.Entry, newSize int) []*raft.Entry {
	return append([]*raft.Entry(nil), a[:newSize]...)
}
