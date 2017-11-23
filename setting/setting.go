package setting

import (
	"github.com/Unknwon/com"
	"github.com/go-macaron/session"
	"github.com/gogap/logrus_mate"
	// Logrus to file
	_ "github.com/gogap/logrus_mate/hooks/file"
	// Logrus to syslog [optional]
	_ "github.com/gogap/logrus_mate/hooks/syslog"
	logrus_fname "github.com/onrik/logrus/filename"
	log "github.com/sirupsen/logrus"
	"gopkg.in/ini.v1"
	"net/mail"
	"net/url"
	"os"
	"os/exec"
	"path"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"
)

// Scheme of type HTTP, HTTPS, etc.
type Scheme string

// Scheme consts
const (
	SchemeHTTP       Scheme = "http"
	SchemeHTTPS      Scheme = "https"
	SchemeFcgi       Scheme = "fcgi"
	SchemeUnixSocket Scheme = "unix"
)

// blah
var (
	// Build infos added by -ldflags
	BuildTime    string
	BuildGitHash string

	// App Settings
	AppVer         string
	AppPath        string
	AppName        string
	AppURL         string
	AppSubURL      string
	AppSubURLDepth int // Number of slashes
	CanRegister    bool
	ProdMode       bool
	NeedsImpressum bool

	// Cron tasks
	Cron struct {
	}

	// Worker configuration
	Worker struct {
		RedisHost string
		RedisDb   string
		RedisPort string
	}

	// Storage configuration
	Storage struct {
		Path string
	}

	AudiowaveformBin string

	// Server settings
	Protocol             Scheme
	UnixSocketPermission uint32
	Domain               string
	HTTPAddr             string
	HTTPPort             string
	DisableRouterLog     bool
	StaticRootPath       string

	HTTP struct {
		AccessControlAllowOrigin string
	}

	// Database Settings
	UseSQLite3    bool
	UseMySQL      bool
	UsePostgreSQL bool
	UseMSSQL      bool

	// Global setting objects
	CustomConf    string
	IsWindows     bool
	Cfg           *ini.File
	HasRobotsTxt  bool
	RobotsTxtPath string

	// Session settings
	SessionConfig  session.Options
	CSRFCookieName string

	// Security settings
	InstallLock             bool
	SecretKey               string
	LoginRememberDays       int
	CookieUserName          string
	CookieRememberName      string
	CookieSecure            bool
	EnableLoginStatusCookie bool
	LoginStatusCookieName   string

	// Cache settings
	CacheAdapter  string
	CacheInterval int
	CacheConn     string

	// i18n settings
	Langs     []string
	Names     []string
	dateLangs map[string]string

	// Markdown sttings
	Markdown struct {
		EnableHardLineBreak bool
		CustomURLSchemes    []string `ini:"CUSTOM_URL_SCHEMES"`
		FileExtensions      []string
	}

	// Smartypants settings
	Smartypants struct {
		Enabled      bool
		Fractions    bool
		Dashes       bool
		LatexDashes  bool
		AngledQuotes bool
	}

	// Bloby manages Static settings
	Bloby struct {
		MaxSizeDisplay int64
		MaxPageDisplay int64
		MaxRawSize     int64
	}

	// Log settings
	LoggerBdd *log.Logger
)

// DateLang transforms standard language locale name to corresponding value in datetime plugin.
func DateLang(lang string) string {
	name, ok := dateLangs[lang]
	if ok {
		return name
	}
	return "en"
}

// execPath returns the executable path.
func execPath() (string, error) {
	file, err := exec.LookPath(os.Args[0])
	if err != nil {
		return "", err
	}
	return filepath.Abs(file)
}

func init() {
	IsWindows = runtime.GOOS == "windows"

	var err error
	if AppPath, err = execPath(); err != nil {
		log.Fatalf("Fail to get app path: %v\n", err)
	}

	// Note: we don't use path.Dir here because it does not handle case
	//	which path starts with two "/" in Windows: "//psf/Home/..."
	AppPath = strings.Replace(AppPath, "\\", "/", -1)
}

func forcePathSeparator(path string) {
	if strings.Contains(path, "\\") {
		log.Fatalf("Do not use '\\' or '\\\\' in paths, instead, please use '/' in all places")
	}
}

// InitConfig to init config from ini file
func InitConfig() {
	workDir, err := WorkDir()
	if err != nil {
		log.Fatalf("Fail to get work directory: %v", err)
	}

	if len(CustomConf) == 0 {
		CustomConf = workDir + "/conf/app.ini"
	}

	initLogging(workDir)

	Cfg, err = ini.Load(CustomConf)
	if err != nil {
		log.Fatalf("Fail to parse '%s': %v", CustomConf, err)
	}
	Cfg.NameMapper = ini.AllCapsUnderscore
	Cfg.BlockMode = false // We don't write anything, speedup cfg reading

	homeDir, err := com.HomeDir()
	if err != nil {
		log.Fatalf("Fail to get home directory: %v", err)
	}
	homeDir = strings.Replace(homeDir, "\\", "/", -1)

	sec := Cfg.Section("server")
	AppName = Cfg.Section("").Key("APP_NAME").MustString("reel2bits")
	AppURL = sec.Key("ROOT_URL").MustString("http://localhost:4000/")
	if AppURL[len(AppURL)-1] != '/' {
		AppURL += "/"
	}

	NeedsImpressum = Cfg.Section("").Key("NEEDS_IMPRESSUM").MustBool(false)

	// Check if has app suburl.
	appURL, err := url.Parse(AppURL)
	if err != nil {
		log.Fatalf("Invalid ROOT_URL '%s': %s", AppURL, err)
	}
	// Suburl should start with '/' and end without '/', such as '/{subpath}'.
	// This value is empty if site does not have sub-url.
	AppSubURL = strings.TrimSuffix(appURL.Path, "/")
	AppSubURLDepth = strings.Count(AppSubURL, "/")

	CanRegister = Cfg.Section("").Key("CAN_REGISTER").MustBool(true)

	Protocol = SchemeHTTP
	if sec.Key("PROTOCOL").String() == "https" {
		Protocol = SchemeHTTPS
		log.Warn("https not supported")
	} else if sec.Key("PROTOCOL").String() == "fcgi" {
		Protocol = SchemeFcgi
		log.Warn("fcgi not supported")
	} else if sec.Key("PROTOCOL").String() == "unix" {
		Protocol = SchemeUnixSocket
		log.Warn("socket not supported")
		UnixSocketPermissionRaw := sec.Key("UNIX_SOCKET_PERMISSION").MustString("666")
		UnixSocketPermissionParsed, err := strconv.ParseUint(UnixSocketPermissionRaw, 8, 32)
		if err != nil || UnixSocketPermissionParsed > 0777 {
			log.Fatalf("Fail to parse unixSocketPermission: %s", UnixSocketPermissionRaw)
		}
		UnixSocketPermission = uint32(UnixSocketPermissionParsed)
	}
	Domain = sec.Key("DOMAIN").MustString("localhost")
	HTTPAddr = sec.Key("HTTP_ADDR").MustString("0.0.0.0")
	HTTPPort = sec.Key("HTTP_PORT").MustString("3000")
	DisableRouterLog = sec.Key("DISABLE_ROUTER_LOG").MustBool()
	StaticRootPath = sec.Key("STATIC_ROOT_PATH").MustString(workDir)

	sec = Cfg.Section("security")
	SecretKey = sec.Key("SECRET_KEY").String()

	sec = Cfg.Section("storage")
	Storage.Path = sec.Key("PATH").MustString(path.Join(workDir, "/uploads"))

	sec = Cfg.Section("audio")
	AudiowaveformBin = sec.Key("AUDIOWAVEFORM_BIN").MustString("/usr/bin/audiowaveform")

	HasRobotsTxt = com.IsFile(path.Join(workDir, "robots.txt"))
	if HasRobotsTxt {
		RobotsTxtPath = path.Join(workDir, "robots.txt")
	}

	Langs = Cfg.Section("i18n").Key("LANGS").Strings(",")
	Names = Cfg.Section("i18n").Key("NAMES").Strings(",")
	dateLangs = Cfg.Section("i18n.datelang").KeysHash()

	sec = Cfg.Section("security")
	InstallLock = sec.Key("INSTALL_LOCK").MustBool()
	SecretKey = sec.Key("SECRET_KEY").String()
	LoginRememberDays = sec.Key("LOGIN_REMEMBER_DAYS").MustInt()
	CookieUserName = sec.Key("COOKIE_USERNAME").String()
	CookieRememberName = sec.Key("COOKIE_REMEMBER_NAME").String()
	CookieSecure = sec.Key("COOKIE_SECURE").MustBool(false)
	EnableLoginStatusCookie = sec.Key("ENABLE_LOGIN_STATUS_COOKIE").MustBool(false)
	LoginStatusCookieName = sec.Key("LOGIN_STATUS_COOKIE_NAME").MustString("login_status")

	ProdMode = Cfg.Section("").Key("RUN_MODE").String() == "prod"

	if err = Cfg.Section("cron").MapTo(&Cron); err != nil {
		log.Fatalf("Fail to map Cron settings: %v", err)
	}
	if err = Cfg.Section("markdown").MapTo(&Markdown); err != nil {
		log.Fatalf("Fail to map Markdown settings: %v", err)
	}
	if err = Cfg.Section("smartypants").MapTo(&Smartypants); err != nil {
		log.Fatalf("Fail to map Smartypants settings: %v", err)
	}
	if err = Cfg.Section("worker").MapTo(&Worker); err != nil {
		log.Fatalf("Fail to map Worker settings: %v", err)
	}

	// Static
	// Max display per file is 2M
	Bloby.MaxSizeDisplay = 2000000
	// Max total page display is max display per file * 2
	Bloby.MaxPageDisplay = Bloby.MaxSizeDisplay * 2
	// Max RAW size authorized (20M)
	Bloby.MaxRawSize = 1000000 * 20

	if len(BuildTime) > 0 {
		log.WithFields(log.Fields{
			"Build Time": BuildTime,
			"Build Hash": BuildGitHash,
		}).Info("Logging enabled")
	} else {
		log.Info("Logging enabled")
	}

	// Make sure everyone gets version info printed.
	log.WithFields(log.Fields{
		"Version": AppVer,
	}).Infof("%s started", AppName)

	initSession()
	initCache()
	initMailer()
}

func initSession() {
	SessionConfig.Provider = Cfg.Section("session").Key("PROVIDER").In("memory",
		[]string{"memory", "file", "redis", "mysql"})
	SessionConfig.ProviderConfig = strings.Trim(Cfg.Section("session").Key("PROVIDER_CONFIG").String(), "\" ")
	SessionConfig.CookieName = Cfg.Section("session").Key("COOKIE_NAME").MustString("i_like_ponies")
	SessionConfig.CookiePath = AppSubURL
	SessionConfig.Secure = Cfg.Section("session").Key("COOKIE_SECURE").MustBool()
	SessionConfig.Gclifetime = Cfg.Section("session").Key("GC_INTERVAL_TIME").MustInt64(3600)
	SessionConfig.Maxlifetime = Cfg.Section("session").Key("SESSION_LIFE_TIME").MustInt64(86400)
	CSRFCookieName = Cfg.Section("session").Key("CSRF_COOKIE_NAME").MustString("_csrf")

	log.Info("Session Service Enabled")
}

func initCache() {
	CacheAdapter = Cfg.Section("cache").Key("ADAPTER").In("memory", []string{"memory", "redis", "memcache"})
	switch CacheAdapter {
	case "memory":
		CacheInterval = Cfg.Section("cache").Key("INTERVAL").MustInt(60)
	case "redis", "memcache":
		CacheConn = strings.Trim(Cfg.Section("cache").Key("HOST").String(), "\" ")
	default:
		log.Fatalf("Unknown cache adapter: %s", CacheAdapter)
	}

	log.Info("Cache Service Enabled")
}

// Mailer represents mail service.
type Mailer struct {
	QueueLength       int
	Subject           string
	Host              string
	From              string
	FromEmail         string
	User, Passwd      string
	DisableHelo       bool
	HeloHostname      string
	SkipVerify        bool
	UseCertificate    bool
	CertFile, KeyFile string
	UsePlainText      bool
}

var (
	// MailService for sending mails
	MailService *Mailer
)

func initMailer() {
	sec := Cfg.Section("mailer")
	// Check mailer setting.
	if !sec.Key("ENABLED").MustBool() {
		log.Info("Mail Service Disabled")
		return
	}

	MailService = &Mailer{
		QueueLength:    sec.Key("SEND_BUFFER_LEN").MustInt(100),
		Subject:        sec.Key("SUBJECT").MustString(AppName),
		Host:           sec.Key("HOST").String(),
		User:           sec.Key("USER").String(),
		Passwd:         sec.Key("PASSWD").String(),
		DisableHelo:    sec.Key("DISABLE_HELO").MustBool(),
		HeloHostname:   sec.Key("HELO_HOSTNAME").String(),
		SkipVerify:     sec.Key("SKIP_VERIFY").MustBool(),
		UseCertificate: sec.Key("USE_CERTIFICATE").MustBool(),
		CertFile:       sec.Key("CERT_FILE").String(),
		KeyFile:        sec.Key("KEY_FILE").String(),
		UsePlainText:   sec.Key("USE_PLAIN_TEXT").MustBool(),
	}
	MailService.From = sec.Key("FROM").MustString(MailService.User)

	if len(MailService.From) > 0 {
		parsed, err := mail.ParseAddress(MailService.From)
		if err != nil {
			log.Fatalf("Invalid mailer.FROM (%s): %v", MailService.From, err)
		}
		MailService.FromEmail = parsed.Address
	}

	log.Info("Mail Service Enabled")
}

func initLogging(workDir string) {
	mate, _ := logrus_mate.NewLogrusMate(logrus_mate.ConfigFile(workDir + "/conf/logging.cfg"))

	filenameHook := logrus_fname.NewHook()
	filenameHook.Field = "source"

	// Set the base logger
	mate.Hijack(
		log.StandardLogger(),
		"app",
	)
	log.AddHook(filenameHook)

	// Set the Database Logger
	LoggerBdd = mate.Logger("bdd")
}

// WorkDir returns absolute path of work directory.
func WorkDir() (string, error) {
	wd := os.Getenv("REEL2BITS_WORK_DIR")
	if len(wd) > 0 {
		return wd, nil
	}

	i := strings.LastIndex(AppPath, "/")
	if i == -1 {
		return AppPath, nil
	}
	return AppPath[:i], nil
}
