package setting

import (
	"github.com/Unknwon/com"
	"github.com/go-macaron/session"
	log "gopkg.in/clog.v1"
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

type Scheme string

const (
	SCHEME_HTTP        Scheme = "http"
	SCHEME_HTTPS       Scheme = "https"
	SCHEME_FCGI        Scheme = "fcgi"
	SCHEME_UNIX_SOCKET Scheme = "unix"
)

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

	// Cron tasks
	Cron struct {
	}

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

	// Log settings
	LogRootPath string
	LogModes    []string
	LogConfigs  []interface{}

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

	// I18n settings
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

	// Static settings
	Bloby struct {
		MaxSizeDisplay int64
		MaxPageDisplay int64
		MaxRawSize     int64
	}
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
	log.New(log.CONSOLE, log.ConsoleConfig{})

	var err error
	if AppPath, err = execPath(); err != nil {
		log.Fatal(2, "Fail to get app path: %v\n", err)
	}

	// Note: we don't use path.Dir here because it does not handle case
	//	which path starts with two "/" in Windows: "//psf/Home/..."
	AppPath = strings.Replace(AppPath, "\\", "/", -1)
}

// WorkDir returns absolute path of work directory.
func WorkDir() (string, error) {
	wd := os.Getenv("GITXT_WORK_DIR")
	if len(wd) > 0 {
		return wd, nil
	}

	i := strings.LastIndex(AppPath, "/")
	if i == -1 {
		return AppPath, nil
	}
	return AppPath[:i], nil
}

func forcePathSeparator(path string) {
	if strings.Contains(path, "\\") {
		log.Fatal(2, "Do not use '\\' or '\\\\' in paths, instead, please use '/' in all places")
	}
}

func InitConfig() {
	workDir, err := WorkDir()
	if err != nil {
		log.Fatal(2, "Fail to get work directory: %v", err)
	}

	if len(CustomConf) == 0 {
		CustomConf = workDir + "/conf/app.ini"
	}

	Cfg, err = ini.Load(CustomConf)
	if err != nil {
		log.Fatal(2, "Fail to parse '%s': %v", CustomConf, err)
	}
	Cfg.NameMapper = ini.AllCapsUnderscore

	homeDir, err := com.HomeDir()
	if err != nil {
		log.Fatal(2, "Fail to get home directory: %v", err)
	}
	homeDir = strings.Replace(homeDir, "\\", "/", -1)

	LogRootPath = Cfg.Section("log").Key("ROOT_PATH").MustString(path.Join(workDir, "log"))
	forcePathSeparator(LogRootPath)

	sec := Cfg.Section("server")
	AppName = Cfg.Section("").Key("APP_NAME").MustString("reel2bits")
	AppURL = sec.Key("ROOT_URL").MustString("http://localhost:4000/")
	if AppURL[len(AppURL)-1] != '/' {
		AppURL += "/"
	}

	// Check if has app suburl.
	appUrl, err := url.Parse(AppURL)
	if err != nil {
		log.Fatal(2, "Invalid ROOT_URL '%s': %s", AppURL, err)
	}
	// Suburl should start with '/' and end without '/', such as '/{subpath}'.
	// This value is empty if site does not have sub-url.
	AppSubURL = strings.TrimSuffix(appUrl.Path, "/")
	AppSubURLDepth = strings.Count(AppSubURL, "/")

	CanRegister = Cfg.Section("").Key("CAN_REGISTER").MustBool(true)

	Protocol = SCHEME_HTTP
	if sec.Key("PROTOCOL").String() == "https" {
		Protocol = SCHEME_HTTPS
		log.Warn("https not supported")
	} else if sec.Key("PROTOCOL").String() == "fcgi" {
		Protocol = SCHEME_FCGI
		log.Warn("fcgi not supported")
	} else if sec.Key("PROTOCOL").String() == "unix" {
		Protocol = SCHEME_UNIX_SOCKET
		log.Warn("socket not supported")
		UnixSocketPermissionRaw := sec.Key("UNIX_SOCKET_PERMISSION").MustString("666")
		UnixSocketPermissionParsed, err := strconv.ParseUint(UnixSocketPermissionRaw, 8, 32)
		if err != nil || UnixSocketPermissionParsed > 0777 {
			log.Fatal(2, "Fail to parse unixSocketPermission: %s", UnixSocketPermissionRaw)
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

	initLogging()

	if err = Cfg.Section("cron").MapTo(&Cron); err != nil {
		log.Fatal(2, "Fail to map Cron settings: %v", err)
	} else if err = Cfg.Section("markdown").MapTo(&Markdown); err != nil {
		log.Fatal(2, "Fail to map Markdown settings: %v", err)
	} else if err = Cfg.Section("smartypants").MapTo(&Smartypants); err != nil {
		log.Fatal(2, "Fail to map Smartypants settings: %v", err)
	}

	// Static
	// Max display per file is 2M
	Bloby.MaxSizeDisplay = 2000000
	// Max total page display is max display per file * 2
	Bloby.MaxPageDisplay = Bloby.MaxSizeDisplay * 2
	// Max RAW size authorized (20M)
	Bloby.MaxRawSize = 1000000 * 20

	initSession()
	initCache()
	initMailer()
}

func initLogging() {
	if len(BuildTime) > 0 {
		log.Trace("Build Time: %s", BuildTime)
		log.Trace("Build Git Hash: %s", BuildGitHash)
	}

	// Because we always create a console logger as primary logger before all settings are loaded,
	// thus if user doesn't set console logger, we should remove it after other loggers are created.
	hasConsole := false

	// Get and check log modes.
	LogModes = strings.Split(Cfg.Section("log").Key("MODE").MustString("console"), ",")
	LogConfigs = make([]interface{}, len(LogModes))
	levelNames := map[string]log.LEVEL{
		"trace": log.TRACE,
		"info":  log.INFO,
		"warn":  log.WARN,
		"error": log.ERROR,
		"fatal": log.FATAL,
	}
	for i, mode := range LogModes {
		mode = strings.ToLower(strings.TrimSpace(mode))
		sec, err := Cfg.GetSection("log." + mode)
		if err != nil {
			log.Fatal(2, "Unknown logger mode: %s", mode)
		}

		validLevels := []string{"trace", "info", "warn", "error", "fatal"}
		name := Cfg.Section("log." + mode).Key("LEVEL").Validate(func(v string) string {
			v = strings.ToLower(v)
			if com.IsSliceContainsStr(validLevels, v) {
				return v
			}
			return "trace"
		})
		level := levelNames[name]

		// Generate log configuration.
		switch log.MODE(mode) {
		case log.CONSOLE:
			hasConsole = true
			LogConfigs[i] = log.ConsoleConfig{
				Level:      level,
				BufferSize: Cfg.Section("log").Key("BUFFER_LEN").MustInt64(100),
			}

		case log.FILE:
			logPath := path.Join(LogRootPath, "gogs.log")
			if err = os.MkdirAll(path.Dir(logPath), os.ModePerm); err != nil {
				log.Fatal(2, "Fail to create log directory '%s': %v", path.Dir(logPath), err)
			}

			LogConfigs[i] = log.FileConfig{
				Level:      level,
				BufferSize: Cfg.Section("log").Key("BUFFER_LEN").MustInt64(100),
				Filename:   logPath,
				FileRotationConfig: log.FileRotationConfig{
					Rotate:   sec.Key("LOG_ROTATE").MustBool(true),
					Daily:    sec.Key("DAILY_ROTATE").MustBool(true),
					MaxSize:  1 << uint(sec.Key("MAX_SIZE_SHIFT").MustInt(28)),
					MaxLines: sec.Key("MAX_LINES").MustInt64(1000000),
					MaxDays:  sec.Key("MAX_DAYS").MustInt64(7),
				},
			}

		case log.SLACK:
			LogConfigs[i] = log.SlackConfig{
				Level:      level,
				BufferSize: Cfg.Section("log").Key("BUFFER_LEN").MustInt64(100),
				URL:        sec.Key("URL").String(),
			}
		}

		log.New(log.MODE(mode), LogConfigs[i])
		log.Trace("Log Mode: %s (%s)", strings.Title(mode), strings.Title(name))
	}

	// Make sure everyone gets version info printed.
	log.Info("%s %s", AppName, AppVer)
	if !hasConsole {
		log.Delete(log.CONSOLE)
	}
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
		log.Fatal(2, "Unknown cache adapter: %s", CacheAdapter)
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
			log.Fatal(2, "Invalid mailer.FROM (%s): %v", MailService.From, err)
		}
		MailService.FromEmail = parsed.Address
	}

	log.Info("Mail Service Enabled")
}
