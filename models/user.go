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
	"github.com/jinzhu/gorm"
	log "github.com/sirupsen/logrus"
	"golang.org/x/crypto/pbkdf2"
	"strings"
	"unicode/utf8"
)

// User struct
type User struct {
	gorm.Model
	UserName  string `gorm:"UNIQUE;NOT NULL"`
	LowerName string `gorm:"UNIQUE;NOT NULL"`
	Email     string `gorm:"NOT NULL"`

	Password string `gorm:"NOT NULL"`
	Rands    string `gorm:"Size:10"`
	Salt     string `gorm:"Size:10"`

	Slug string `gorm:"UNIQUE"`

	// Permissions
	Admin  uint `gorm:"DEFAULT:2"` // See models.BoolFalse
	Active uint `gorm:"DEFAULT:2"` // See models.BoolFalse
}

// IsAdmin from FakeBool
func (user *User) IsAdmin() bool {
	realBool, _ := isABool(user.Admin, BoolFalse)
	return realBool
}

// IsActive from FakeBool
func (user *User) IsActive() bool {
	realBool, _ := isABool(user.Active, BoolFalse)
	return realBool
}

// BeforeSave Create slug
func (user *User) BeforeSave() (err error) {
	user.Slug = slug.Make(user.UserName)
	return nil
}

// BeforeUpdate Update slug
func (user *User) BeforeUpdate() (err error) {
	user.Slug = slug.Make(user.UserName)
	return nil
}

func countUsers(db *gorm.DB) (count int64) {
	db.Model(&User{}).Select("id").Count(&count)
	return
}

// CountUsers returns number of users.
func CountUsers() int64 {
	return countUsers(db)
}

// GetUserBySlug or error
func GetUserBySlug(slug string) (user User, err error) {
	err = db.Where(&User{Slug: slug}).First(&user).Error
	if gorm.IsRecordNotFoundError(err) || user.ID == 0 {
		return user, errors.UserNotExist{UserID: 0, Name: slug}
	} else if err != nil {
		return user, err
	}
	return
}

func getUserByID(id uint) (user User, err error) {
	err = db.Where("id = ?", id).First(&user).Error
	if gorm.IsRecordNotFoundError(err) || user.ID == 0 {
		return user, errors.UserNotExist{UserID: id, Name: ""}
	} else if err != nil {
		return user, err
	}
	return
}

// GetUserByID returns the user object by given ID if exists.
func GetUserByID(id uint) (User, error) {
	return getUserByID(id)
}

// GetUserByName returns user by given name.
func GetUserByName(name string) (user User, err error) {
	if len(name) == 0 {
		return user, errors.UserNotExist{UserID: 0, Name: name}
	}
	err = db.Where("lower_name = ?", strings.ToLower(name)).First(&user).Error
	if gorm.IsRecordNotFoundError(err) || user.ID == 0 {
		return user, errors.UserNotExist{UserID: 0, Name: name}
	} else if err != nil {
		return user, err
	}
	return
}

// GetUserByEmail returns the user object by given e-mail if exists.
func GetUserByEmail(email string) (user User, err error) {
	if len(email) == 0 {
		return user, errors.UserNotExist{UserID: 0, Name: email}
	}
	err = db.Where("email = ?", strings.ToLower(email)).First(&user).Error
	if gorm.IsRecordNotFoundError(err) || user.ID == 0 {
		return user, errors.UserNotExist{UserID: 0, Name: email}
	} else if err != nil {
		return user, err
	}
	return
}

// IsUserExist checks if given user name exist,
// the user name should be noncased unique.
// If uid is presented, then check will rule out that one,
// it is used when update a user name in settings page.
func IsUserExist(uid int64, name string) (exist bool, err error) {
	if len(name) == 0 {
		return false, nil
	}
	user := User{}
	err = db.Where("id != ?", uid).Where(&User{LowerName: strings.ToLower(name)}).First(&user).Error
	if gorm.IsRecordNotFoundError(err) || user.ID == 0 {
		return false, nil
	} else if err != nil {
		return false, nil
	}
	return true, nil
}

// GetFirstUser only
func GetFirstUser() (user User, err error) {
	err = db.Order("id ASC").First(&user).Error
	if gorm.IsRecordNotFoundError(err) || user.ID == 0 {
		return user, errors.UserNotExist{UserID: 1, Name: ""}
	} else if err != nil {
		return user, err
	}
	return
}

var (
	reservedUsernames = []string{"anon", "anonymous", "private", "assets", "css", "img", "js", "less", "plugins",
		"debug", "raw", "install", "api", "avatar", "user", "org", "help", "stars", "issues", "pulls",
		"commits", "repo", "template", "admin", "new", ".", ".."}
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

// CreateUser and do some validation
func CreateUser(user *User) (err error) {
	if err = IsUsableUsername(user.UserName); err != nil {
		return err
	}

	isExist, err := IsUserExist(0, user.UserName)
	if err != nil {
		return err
	} else if isExist {
		return ErrUserAlreadyExist{user.UserName}
	}

	user.Email = strings.ToLower(user.Email)
	user.LowerName = strings.ToLower(user.UserName)

	if user.Rands, err = GetUserSalt(); err != nil {
		return err
	}
	if user.Salt, err = GetUserSalt(); err != nil {
		return err
	}
	user.EncodePasswd()

	tx := db.Begin()
	defer func() {
		if r := recover(); r != nil {
			tx.Rollback()
		}
	}()

	if tx.Error != nil {
		return err
	}

	if err := tx.Create(user).Error; err != nil {
		tx.Rollback()
		return err
	}

	if err := tx.Commit().Error; err != nil {
		return err
	}

	return err
}

// Update an user
func updateUser(db *gorm.DB, user *User) (err error) {
	tx := db.Begin()
	defer func() {
		if r := recover(); r != nil {
			tx.Rollback()
		}
	}()

	if tx.Error != nil {
		return err
	}

	if err := tx.Save(user).Error; err != nil {
		tx.Rollback()
		return err
	}

	if err := tx.Commit().Error; err != nil {
		return err
	}

	return err
}

// UpdateUser with datas
func UpdateUser(u *User) error {
	return updateUser(db, u)
}

// UserLogin validates user name and password.
func UserLogin(username, password string) (user *User, err error) {
	if strings.Contains(username, "@") {
		user = &User{Email: strings.ToLower(username)}
	} else {
		user = &User{LowerName: strings.ToLower(username)}
	}

	err = db.Where(user).First(&user).Error
	if gorm.IsRecordNotFoundError(err) {
		return nil, errors.UserNotExist{UserID: user.ID, Name: user.UserName}
	} else if err != nil {
		return nil, err
	}

	if user.ValidatePassword(password) {
		return user, nil
	}

	return nil, errors.UserNotExist{UserID: user.ID, Name: user.UserName}

}

// get user by verify code
func getVerifyUser(code string) (user User) {
	if len(code) <= tool.TimeLimitCodeLength {
		return user
	}

	// use tail hex username query user
	hexStr := code[tool.TimeLimitCodeLength:]
	if b, err := hex.DecodeString(hexStr); err == nil {
		if user, err = GetUserByName(string(b)); user.ID > 0 {
			return user
		} else if !errors.IsUserNotExist(err) {
			log.Errorf("GetUserByName: %v", err)
		}
	}

	return user
}

// VerifyUserActiveCode when active account
func VerifyUserActiveCode(code string) (user User) {
	// HARDCODED
	minutes := 180

	if user = getVerifyUser(code); user.ID > 0 {
		// time limit code
		prefix := code[:tool.TimeLimitCodeLength]
		data := com.ToStr(user.ID) + user.Email + user.LowerName + user.Password + user.Rands

		if tool.VerifyTimeLimitCode(data, minutes, prefix) {
			return user
		}
	}
	return user
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

// ID id
func (mUser mailerUser) ID() uint {
	return mUser.user.ID
}

// Email func
func (mUser mailerUser) Email() string {
	return mUser.user.Email
}

// DisplayName func
func (mUser mailerUser) DisplayName() string {
	return mUser.user.UserName
}

// GenerateActivateCode func
func (mUser mailerUser) GenerateActivateCode() string {
	return mUser.user.GenerateActivateCode()
}

// GenerateEmailActivateCode func
func (mUser mailerUser) GenerateEmailActivateCode(email string) string {
	return mUser.user.GenerateEmailActivateCode(email)
}

// NewMailerUser mail user
func NewMailerUser(u *User) mailer.User {
	return mailerUser{u}
}
