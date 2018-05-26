package form

import (
	"dev.sigpipe.me/dashie/reel2bits/pkg/tool"
	"fmt"
	"github.com/Unknwon/com"
	"github.com/go-macaron/binding"
	"github.com/leonelquinteros/gotext"
	log "github.com/sirupsen/logrus"
	"gopkg.in/macaron.v1"
	"io/ioutil"
	"mime/multipart"
	"reflect"
	"regexp"
	"strings"
)

const errAlphaDashDotSlash = "AlphaDashDotSlashError"
const errOnlyAudioFile = "OnlyAudioFileError"

var alphaDashDotSlashPattern = regexp.MustCompile("[^\\d\\w-_\\./]")

func init() {
	binding.SetNameMapper(com.ToSnakeCase)
	binding.AddRule(&binding.Rule{
		IsMatch: func(rule string) bool {
			return rule == "AlphaDashDotSlash"
		},
		IsValid: func(errs binding.Errors, name string, v interface{}) (bool, binding.Errors) {
			if alphaDashDotSlashPattern.MatchString(fmt.Sprintf("%v", v)) {
				errs.Add([]string{name}, errAlphaDashDotSlash, "AlphaDashDotSlash")
				return false, errs
			}
			return true, errs
		},
	})

	binding.AddRule(&binding.Rule{
		IsMatch: func(rule string) bool {
			return rule == "OnlyAudioFile"
		},
		IsValid: func(errs binding.Errors, name string, v interface{}) (bool, binding.Errors) {
			fr, err := v.(*multipart.FileHeader).Open()
			if err != nil {
				log.Errorf("Error opening temp uploaded file to read content: %s", err)
				errs.Add([]string{name}, errOnlyAudioFile, "OnlyAudioFile")
				return false, errs
			}
			defer fr.Close()

			data, err := ioutil.ReadAll(fr)
			if err != nil {
				log.Errorf("Error reading temp uploaded file: %s", err)
				errs.Add([]string{name}, errOnlyAudioFile, "OnlyAudioFile")
				return false, errs
			}

			mimetype, err := tool.GetBlobMimeType(data)
			if err != nil {
				log.Errorf("Error reading temp uploaded file: %s", err)
				errs.Add([]string{name}, errOnlyAudioFile, "OnlyAudioFile")
				return false, errs
			}
			log.Debugf("Got mimetype %s for file %s", mimetype, v.(*multipart.FileHeader).Filename)

			if mimetype != "audio/mpeg" && mimetype != "audio/x-wav" && mimetype != "audio/ogg" && mimetype != "audio/x-flac" {
				errs.Add([]string{name}, errOnlyAudioFile, "OnlyAudioFile")
				return false, errs
			}

			return true, errs
		},
	})
}

// Form interface for binding validator
type Form interface {
	binding.Validator
}

// Assign assign form values back to the template data.
func Assign(form interface{}, data map[string]interface{}) {
	typ := reflect.TypeOf(form)
	val := reflect.ValueOf(form)

	if typ.Kind() == reflect.Ptr {
		typ = typ.Elem()
		val = val.Elem()
	}

	for i := 0; i < typ.NumField(); i++ {
		field := typ.Field(i)

		fieldName := field.Tag.Get("form")
		// Allow ignored fields in the struct
		if fieldName == "-" {
			continue
		} else if len(fieldName) == 0 {
			fieldName = com.ToSnakeCase(field.Name)
		}

		data[fieldName] = val.Field(i).Interface()
	}
}

func getRuleBody(field reflect.StructField, prefix string) string {
	for _, rule := range strings.Split(field.Tag.Get("binding"), ";") {
		if strings.HasPrefix(rule, prefix) {
			return rule[len(prefix) : len(rule)-1]
		}
	}
	return ""
}

func getSize(field reflect.StructField) string {
	return getRuleBody(field, "Size(")
}

func getMinSize(field reflect.StructField) string {
	return getRuleBody(field, "MinSize(")
}

func getMaxSize(field reflect.StructField) string {
	return getRuleBody(field, "MaxSize(")
}

func getInclude(field reflect.StructField) string {
	return getRuleBody(field, "Include(")
}

func getIn(field reflect.StructField) string {
	return getRuleBody(field, "In(")
}

func validate(errs binding.Errors, data map[string]interface{}, f Form, l macaron.Locale) binding.Errors {
	log.Debug("Validating form")

	if errs.Len() == 0 {
		return errs
	}

	data["HasError"] = true
	Assign(f, data)

	typ := reflect.TypeOf(f)
	val := reflect.ValueOf(f)

	if typ.Kind() == reflect.Ptr {
		typ = typ.Elem()
		val = val.Elem()
	}

	for i := 0; i < typ.NumField(); i++ {
		field := typ.Field(i)

		fieldName := field.Tag.Get("form")
		// Allow ignored fields in the struct
		if fieldName == "-" {
			continue
		}

		if errs[0].FieldNames[0] == field.Name {
			data["Err_"+field.Name] = true

			trName := field.Tag.Get("locale")
			if len(trName) == 0 {
				trName = gotext.Get("form." + field.Name)
			} else {
				trName = gotext.Get(trName)
			}

			switch errs[0].Classification {
			case binding.ERR_REQUIRED:
				data["ErrorMsg"] = trName + gotext.Get(" cannot be empty.")
			case binding.ERR_ALPHA_DASH:
				data["ErrorMsg"] = trName + gotext.Get(" must be valid alpha or numeric or dash(-_) characters.")
			case binding.ERR_ALPHA_DASH_DOT:
				data["ErrorMsg"] = trName + gotext.Get(" must be valid alpha or numeric or dash(-_) or dot characters.")
			case errAlphaDashDotSlash:
				data["ErrorMsg"] = trName + gotext.Get(" must be valid alpha or numeric or dash(-_) or dot characters or slashes.")
			case errOnlyAudioFile:
				data["ErrorMsg"] = trName + gotext.Get(" must be a supported audio file")
			case binding.ERR_SIZE:
				data["ErrorMsg"] = trName + gotext.Get(" must be size %s.", getSize(field))
			case binding.ERR_MIN_SIZE:
				data["ErrorMsg"] = trName + gotext.Get(" must contain at least %s characters.", getMinSize(field))
			case binding.ERR_MAX_SIZE:
				data["ErrorMsg"] = trName + gotext.Get(" must contain at most %s characters.", getMaxSize(field))
			case binding.ERR_EMAIL:
				data["ErrorMsg"] = trName + gotext.Get("Invalid email format.")
			case binding.ERR_URL:
				data["ErrorMsg"] = trName + gotext.Get(" is not a valid URL.")
			case binding.ERR_INCLUDE:
				data["ErrorMsg"] = trName + gotext.Get(" must contain substring '%s'.", getInclude(field))
			case binding.ERR_IN:
				data["ErrorMsg"] = trName + gotext.Get(" must be one of: %s.", getIn(field))
			default:
				data["ErrorMsg"] = gotext.Get("Unknown error: ") + " " + errs[0].Classification
			}
			return errs
		}
	}
	return errs
}
