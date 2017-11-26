package errors

import "errors"

// New is a wrapper of real errors.New function.
func New(text string) error {
	return errors.New(text)
}
