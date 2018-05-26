package errors

import "fmt"

// EmptyName is empty
type EmptyName struct{}

// IsEmptyName empty
func IsEmptyName(err error) bool {
	_, ok := err.(EmptyName)
	return ok
}

func (err EmptyName) Error() string {
	return "empty name"
}

// UserNotExist struct
type UserNotExist struct {
	UserID uint
	Name   string
}

// IsUserNotExist bool
func IsUserNotExist(err error) bool {
	_, ok := err.(UserNotExist)
	return ok
}

func (err UserNotExist) Error() string {
	return fmt.Sprintf("user does not exist [user_id: %d, name: %s]", err.UserID, err.Name)
}
