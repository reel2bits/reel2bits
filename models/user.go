package models

import (
	"crypto/sha256"
	"crypto/subtle"
	"dev.sigpipe.me/dashie/reel2bits/models/errors"
	"dev.sigpipe.me/dashie/reel2bits/pkg/mailer"
	"dev.sigpipe.me/dashie/reel2bits/pkg/tool"
	"encoding/hex"
	"fmt"
	"github.com/Unknwon/com"
	"github.com/gosimple/slug"
	"golang.org/x/crypto/pbkdf2"
	log "gopkg.in/clog.v1"
	"strings"
	"time"
	"unicode/utf8"
)

// User database structure
type User struct {
	ID        int64  `xorm:"pk autoincr"`
	UserName  string `xorm:"UNIQUE NOT NULL"`
	LowerName string `xorm:"UNIQUE NOT NULL"`
	Email     string `xorm:"NOT NULL"`

	Slug string `xorm:"UNIQUE"`

	Password string `xorm:"NOT NULL"`
	Rands    string `xorm:"VARCHAR(10)"`
	Salt     string `xorm:"VARCHAR(10)"`

	// Permissions
	IsAdmin  bool `xorm:"DEFAULT 0"`
	IsActive bool `xorm:"DEFAULT 0"`

	Created     time.Time `xorm:"-"`
	CreatedUnix int64
	Updated     time.Time `xorm:"-"`
	UpdatedUnix int64

	// Relations
	// 	Track
}

// BeforeInsert set times and slug
func (user *User) BeforeInsert() {
	user.CreatedUnix = time.Now().Unix()
	user.UpdatedUnix = user.CreatedUnix
	user.Slug = slug.Make(user.UserName)
}

// BeforeUpdate set times
func (user *User) BeforeUpdate() {
	user.UpdatedUnix = time.Now().Unix()
	user.Slug = slug.Make(user.UserName)
}

func countUsers(e Engine) int64 {
	count, _ := x.Count(new(User))
	return count
}

// CountUsers returns number of users.
func CountUsers() int64 {
	return countUsers(x)
}

func getUserByID(e Engine, id int64) (*User, error) {
	u := new(User)
	has, err := e.Id(id).Get(u)
	if err != nil {
		return nil, err
	} else if !has {
		return nil, errors.UserNotExist{id, ""}
	}
	return u, nil
}

// GetUserByID returns the user object by given ID if exists.
func GetUserByID(id int64) (*User, error) {
	return getUserByID(x, id)
}

// GetUserByName returns user by given name.
func GetUserByName(name string) (*User, error) {
	if len(name) == 0 {
		return nil, errors.UserNotExist{0, name}
	}
	u := &User{LowerName: strings.ToLower(name)}
	has, err := x.Get(u)
	if err != nil {
		return nil, err
	} else if !has {
		return nil, errors.UserNotExist{0, name}
	}
	return u, nil
}

// GetUserByEmail returns the user object by given e-mail if exists.
func GetUserByEmail(email string) (*User, error) {
	if len(email) == 0 {
		return nil, errors.UserNotExist{0, "email"}
	}

	email = strings.ToLower(email)
	user := &User{Email: email}
	has, err := x.Get(user)
	if err != nil {
		return nil, err
	}
	if has {
		return user, nil
	}

	return nil, errors.UserNotExist{0, email}
}

// GetUserBySlug or error
func GetUserBySlug(slug string) (*User, error) {
	if len(slug) == 0 {
		return nil, errors.UserNotExist{0, "slug"}
	}

	user := &User{Slug: slug}
	has, err := x.Get(user)
	if err != nil {
		return nil, err
	}
	if has {
		return user, nil
	}

	return nil, errors.UserNotExist{0, slug}
}

// IsUserExist checks if given user name exist,
// the user name should be noncased unique.
// If uid is presented, then check will rule out that one,
// it is used when update a user name in settings page.
func IsUserExist(uid int64, name string) (bool, error) {
	if len(name) == 0 {
		return false, nil
	}
	return x.Where("id != ?", uid).Get(&User{LowerName: strings.ToLower(name)})
}

var (
	reservedUsernames = []string{"anon", "anonymous", "private", "assets", "css", "img", "js", "less",
		"plugins", "debug", "raw", "install", "api", "avatar", "user", "org", "help", "stars", "issues",
		"pulls", "commits", "repo", "template", "admin", "new", "track", "album", "set", "upload",
		".", ".."}
	reservedUserPatterns = []string{"*.keys"}
)

// isUsableName checks if name is reserved or pattern of name is not allowed
// based on given reserved names and patterns.
// Names are exact match, patterns can be prefix or suffix match with placeholder '*'.
func isUsableName(names, patterns []string, name string) error {
	name = strings.TrimSpace(strings.ToLower(name))
	if utf8.RuneCountInString(name) == 0 {
		return errors.EmptyName{}
	}

	for i := range names {
		if name == names[i] {
			return ErrNameReserved{name}
		}
	}

	for _, pat := range patterns {
		if pat[0] == '*' && strings.HasSuffix(name, pat[1:]) ||
			(pat[len(pat)-1] == '*' && strings.HasPrefix(name, pat[:len(pat)-1])) {
			return ErrNamePatternNotAllowed{pat}
		}
	}

	return nil
}

// IsUsableUsername or not
func IsUsableUsername(name string) error {
	return isUsableName(reservedUsernames, reservedUserPatterns, name)
}

// EncodePasswd encodes password to safe format.
func (user *User) EncodePasswd() {
	newPasswd := pbkdf2.Key([]byte(user.Password), []byte(user.Salt), 10000, 50, sha256.New)
	user.Password = fmt.Sprintf("%x", newPasswd)
}

// ValidatePassword checks if given password matches the one belongs to the user.
func (user *User) ValidatePassword(passwd string) bool {
	newUser := &User{Password: passwd, Salt: user.Salt}
	newUser.EncodePasswd()
	return subtle.ConstantTimeCompare([]byte(user.Password), []byte(newUser.Password)) == 1
}

// GetUserSalt returns a ramdom user salt token.
func GetUserSalt() (string, error) {
	return tool.RandomString(10)
}

// CreateUser a new user and do some validation
func CreateUser(u *User) (err error) {
	if err = IsUsableUsername(u.UserName); err != nil {
		return err
	}

	isExist, err := IsUserExist(0, u.UserName)
	if err != nil {
		return err
	} else if isExist {
		return ErrUserAlreadyExist{u.UserName}
	}

	u.Email = strings.ToLower(u.Email)
	u.LowerName = strings.ToLower(u.UserName)

	if u.Rands, err = GetUserSalt(); err != nil {
		return err
	}
	if u.Salt, err = GetUserSalt(); err != nil {
		return err
	}
	u.EncodePasswd()

	sess := x.NewSession()
	defer sessionRelease(sess)
	if err = sess.Begin(); err != nil {
		return err
	}

	if _, err = sess.Insert(u); err != nil {
		return err
	}

	return sess.Commit()
}

func updateUser(e Engine, u *User) error {
	u.LowerName = strings.ToLower(u.UserName)
	u.Email = strings.ToLower(u.Email)
	_, err := e.Id(u.ID).AllCols().Update(u)
	return err
}

// UpdateUser an user
func UpdateUser(u *User) error {
	return updateUser(x, u)
}

// UserLogin validates user name and password.
func UserLogin(username, password string) (*User, error) {
	var user *User
	if strings.Contains(username, "@") {
		user = &User{Email: strings.ToLower(username)}
	} else {
		user = &User{LowerName: strings.ToLower(username)}
	}

	hasUser, err := x.Get(user)
	if err != nil {
		return nil, err
	}

	if hasUser {
		if user.ValidatePassword(password) {
			return user, nil
		}

		return nil, errors.UserNotExist{user.ID, user.UserName}
	}

	return nil, errors.UserNotExist{user.ID, user.UserName}
}

// get user by verify code
func getVerifyUser(code string) (user *User) {
	if len(code) <= tool.TimeLimitCodeLength {
		return nil
	}

	// use tail hex username query user
	hexStr := code[tool.TimeLimitCodeLength:]
	if b, err := hex.DecodeString(hexStr); err == nil {
		if user, err = GetUserByName(string(b)); user != nil {
			return user
		} else if !errors.IsUserNotExist(err) {
			log.Error(2, "GetUserByName: %v", err)
		}
	}

	return nil
}

// VerifyUserActiveCode when active account
func VerifyUserActiveCode(code string) (user *User) {
	// HARDCODED
	minutes := 180

	if user = getVerifyUser(code); user != nil {
		// time limit code
		prefix := code[:tool.TimeLimitCodeLength]
		data := com.ToStr(user.ID) + user.Email + user.LowerName + user.Password + user.Rands

		if tool.VerifyTimeLimitCode(data, minutes, prefix) {
			return user
		}
	}
	return nil
}

// GenerateEmailActivateCode generates an activate code based on user information and given e-mail.
func (user *User) GenerateEmailActivateCode(email string) string {
	code := tool.CreateTimeLimitCode(
		com.ToStr(user.ID)+email+user.LowerName+user.Password+user.Rands, 180, nil)

	// Add tail hex username
	code += hex.EncodeToString([]byte(user.LowerName))
	return code
}

// GenerateActivateCode generates an activate code based on user information.
func (user *User) GenerateActivateCode() string {
	return user.GenerateEmailActivateCode(user.Email)
}

// mailerUser is a wrapper for satisfying mailer.User interface.
type mailerUser struct {
	user *User
}

func (mu mailerUser) ID() int64 {
	return mu.user.ID
}

func (mu mailerUser) Email() string {
	return mu.user.Email
}

func (mu mailerUser) DisplayName() string {
	return mu.user.UserName
}

func (mu mailerUser) GenerateActivateCode() string {
	return mu.user.GenerateActivateCode()
}

func (mu mailerUser) GenerateEmailActivateCode(email string) string {
	return mu.user.GenerateEmailActivateCode(email)
}

// NewMailerUser initiate a new mailer for the user
func NewMailerUser(u *User) mailer.User {
	return mailerUser{u}
}
