package errors

import "fmt"

type RepoNotExist struct {
	ID     int64
	UserID   int64
	Name   string
}

func IsRepoNotExist(err error) bool {
	_, ok := err.(RepoNotExist)
	return ok
}

func (err RepoNotExist) Error() string {
	return fmt.Sprintf("repository does not exist [id: %d, user_id: %d, name: %s]", err.ID, err.UserID, err.Name)
}
