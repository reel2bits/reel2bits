package models

import (
	"dev.sigpipe.me/dashie/reel2bits/setting"
	"errors"
	"fmt"
	"github.com/jinzhu/gorm"
	log "github.com/sirupsen/logrus"
	"net/url"
	"os"
	"path"
	"strings"
	// mysql
	_ "github.com/jinzhu/gorm/dialects/mysql"
	// postgresql
	_ "github.com/jinzhu/gorm/dialects/postgres"
	// sqlite
	_ "github.com/jinzhu/gorm/dialects/sqlite"
	// mssql
	_ "github.com/jinzhu/gorm/dialects/mssql"
)

// Vars
var (
	db        *gorm.DB
	HasEngine bool

	DbCfg struct {
		Type, Host, Name, User, Passwd, Path, SSLMode string
		Logging                                       bool
	}

	EnableSQLite3 bool
)

// START OF CRIMEs
// Yes I know, this is ugly, please don't revoke my Developper License©
// The issue is that in Go, 0 == false == nil == empty, they are all considered empties.
// So we got into the issue where with Gorm we can't query like .Where("is_ready = ?", false) because issues
// So we decided to use integers.
const (
	// Please
	BoolTrue = 1 // don't
	// change
	BoolFalse = 2 // the
	// integers, because we will have the integer value hardcoded into the IsXxx() function, and the `xxx` comment
)

// The database field will looks like :
// Ready uint
// And it will have a "IsReady" function, which will return a real bool, according to the uint value.
// As for the default, well, it will be hardcoded in the function, and in the `xxx:"DEFAULT:y"` comment

func isABool(fakeBool uint, defaultBool uint) (bool, error) {
	switch fakeBool {
	case BoolTrue:
		return true, nil
	case BoolFalse:
		return false, nil
	default:
		if defaultBool == BoolTrue {
			return true, nil
		} else if defaultBool == BoolFalse {
			return false, nil
		}
		return false, fmt.Errorf("%d is not a valid FakeBool", defaultBool)
	}
}

func boolToFake(realBool bool) uint {
	if realBool {
		return BoolTrue
	}
	return BoolFalse
}

// BoolToFake because :shrug:
func BoolToFake(realBool bool) uint {
	return boolToFake(realBool)
}

// END OF CRIMES

// LoadConfigs to init db
func LoadConfigs() {
	sec := setting.Cfg.Section("database")
	DbCfg.Type = sec.Key("DB_TYPE").String()
	switch DbCfg.Type {
	case "sqlite3":
		setting.UseSQLite3 = true
	case "mysql":
		setting.UseMySQL = true
	case "postgres":
		setting.UsePostgreSQL = true
	case "mssql":
		setting.UseMSSQL = true
	}
	DbCfg.Host = sec.Key("HOST").String()
	DbCfg.Name = sec.Key("NAME").String()
	DbCfg.User = sec.Key("USER").String()
	if len(DbCfg.Passwd) == 0 {
		DbCfg.Passwd = sec.Key("PASSWD").String()
	}
	DbCfg.SSLMode = sec.Key("SSL_MODE").String()
	DbCfg.Path = sec.Key("PATH").MustString("bleurg.db")
	DbCfg.Logging = sec.Key("LOGGING").MustBool(true)
}

// parsePostgreSQLHostPort parses given input in various forms defined in
// https://www.postgresql.org/docs/current/static/libpq-connect.html#LIBPQ-CONNSTRING
// and returns proper host and port number.
func parsePostgreSQLHostPort(info string) (string, string) {
	host, port := "127.0.0.1", "5432"
	if strings.Contains(info, ":") && !strings.HasSuffix(info, "]") {
		idx := strings.LastIndex(info, ":")
		host = info[:idx]
		port = info[idx+1:]
	} else if len(info) > 0 {
		host = info
	}
	return host, port
}

func parseMSSQLHostPort(info string) (string, string) {
	host, port := "127.0.0.1", "1433"
	if strings.Contains(info, ":") {
		host = strings.Split(info, ":")[0]
		port = strings.Split(info, ":")[1]
	} else if strings.Contains(info, ",") {
		host = strings.Split(info, ",")[0]
		port = strings.TrimSpace(strings.Split(info, ",")[1])
	} else if len(info) > 0 {
		host = info
	}
	return host, port
}

func getEngine() (*gorm.DB, error) {
	connStr := ""
	var Param = "?"
	if strings.Contains(DbCfg.Name, Param) {
		Param = "&"
	}
	switch DbCfg.Type {
	case "mysql":
		// "user:password@/dbname?charset=utf8&parseTime=True&loc=Local"
		if DbCfg.Host[0] == '/' { // looks like a unix socket
			connStr = fmt.Sprintf("%s:%s@unix(%s)/%s%scharset=utf8&parseTime=true",
				DbCfg.User, DbCfg.Passwd, DbCfg.Host, DbCfg.Name, Param)
		} else {
			connStr = fmt.Sprintf("%s:%s@tcp(%s)/%s%scharset=utf8&parseTime=true",
				DbCfg.User, DbCfg.Passwd, DbCfg.Host, DbCfg.Name, Param)
		}
	case "postgres":
		// "host=myhost port=myport user=gorm dbname=gorm password=mypassword"
		host, port := parsePostgreSQLHostPort(DbCfg.Host)
		if host[0] == '/' { // looks like a unix socket
			connStr = fmt.Sprintf("postgres://%s:%s@:%s/%s%ssslmode=%s&host=%s",
				url.QueryEscape(DbCfg.User), url.QueryEscape(DbCfg.Passwd), port, DbCfg.Name, Param, DbCfg.SSLMode, host)
		} else {
			connStr = fmt.Sprintf("postgres://%s:%s@%s:%s/%s%ssslmode=%s",
				url.QueryEscape(DbCfg.User), url.QueryEscape(DbCfg.Passwd), host, port, DbCfg.Name, Param, DbCfg.SSLMode)
		}
	case "mssql":
		// "sqlserver://username:password@localhost:1433?database=dbname"
		host, port := parseMSSQLHostPort(DbCfg.Host)
		connStr = fmt.Sprintf("server=%s; port=%s; database=%s; user id=%s; password=%s;", host, port, DbCfg.Name, DbCfg.User, DbCfg.Passwd)
	case "sqlite3":
		if !EnableSQLite3 {
			return nil, errors.New("this binary version does not build support for SQLite3")
		}
		if err := os.MkdirAll(path.Dir(DbCfg.Path), os.ModePerm); err != nil {
			return nil, fmt.Errorf("fail to create directories: %v", err)
		}
		connStr = "file:" + DbCfg.Path + "?cache=shared&mode=rwc"
	default:
		return nil, fmt.Errorf("unknown database type: %s", DbCfg.Type)
	}
	return gorm.Open(DbCfg.Type, connStr)
}

// SetEngine to use
func SetEngine() (err error) {
	db, err = getEngine()
	if err != nil {
		return fmt.Errorf("fail to connect to database: %v", err)
	}

	db.LogMode(DbCfg.Logging)
	//db.SetLogger(setting.LoggerBdd)
	return nil
}

// NewEngine to use
func NewEngine() (err error) {
	if err = SetEngine(); err != nil {
		return err
	}

	db.AutoMigrate(&User{}, &Album{}, &Track{}, &TrackInfo{}, &TimelineItem{})

	return nil
}

// Ping pong
func Ping() error {
	return db.DB().Ping()
}

// InitDb from config
func InitDb() {
	LoadConfigs()

	if err := NewEngine(); err != nil {
		log.Fatalf("Fail to initialize ORM engine: %v", err)
	}
	HasEngine = true

	if EnableSQLite3 {
		log.Info("SQLite3 Supported")
	}
}
