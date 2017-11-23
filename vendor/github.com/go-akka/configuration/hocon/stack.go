package hocon

import (
	"errors"
	"sync"
)

type Stack struct {
	lock   sync.Mutex
	values []int
}

func NewStack() *Stack {
	return &Stack{sync.Mutex{}, make([]int, 0)}
}

func (p *Stack) Push(v int) {
	p.lock.Lock()
	defer p.lock.Unlock()

	p.values = append(p.values, v)
}

func (p *Stack) Pop() (int, error) {
	p.lock.Lock()
	defer p.lock.Unlock()

	l := len(p.values)
	if l == 0 {
		return 0, errors.New("Empty Stack")
	}

	res := p.values[l-1]
	p.values = p.values[:l-1]
	return res, nil
}
