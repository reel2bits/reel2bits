package cmd

import (
	"dev.sigpipe.me/dashie/reel2bits/models"
	"dev.sigpipe.me/dashie/reel2bits/pkg/mailer"
	"dev.sigpipe.me/dashie/reel2bits/setting"
	"fmt"
	"github.com/peterh/liner"
	log "github.com/sirupsen/logrus"
	"github.com/urfave/cli"
)

// CreateUser cli target
var CreateUser = cli.Command{
	Name:        "createuser",
	Usage:       "Create an user",
	Description: "It permits creating an user",
	Action:      runCreateUser,
	Flags: []cli.Flag{
		stringFlag("config, c", "config/app.ini", "Custom config file path"),
	},
}

func runCreateUser(ctx *cli.Context) error {
	if ctx.IsSet("config") {
		setting.CustomConf = ctx.String("config")
	}

	setting.InitConfig()
	models.InitDb()
	mailer.NewContext()

	line := liner.NewLiner()
	defer line.Close()

	line.SetCtrlCAborts(true)

	username, err := line.Prompt("Username ? ")
	if err == liner.ErrPromptAborted {
		log.Print("Aborted")
	} else if err != nil {
		log.Errorf("error reading line: %v", err)
		return fmt.Errorf("error reading line: %v", err)
	}

	email, err := line.Prompt("Email ? ")
	if err == liner.ErrPromptAborted {
		log.Print("Aborted")
	} else if err != nil {
		log.Errorf("error reading line: %v", err)
		return fmt.Errorf("error reading line: %v", err)
	}

	password, err := line.PasswordPrompt("Password ? ")
	if err == liner.ErrPromptAborted {
		log.Print("Aborted")
	} else if err != nil {
		log.Errorf("error reading line: %v", err)
		return fmt.Errorf("error reading line: %v", err)
	}

	u := &models.User{
		UserName: username,
		Email:    email,
		Password: password,
		Active:   models.BoolToFake(true), // FIXME: implement user activation by email
	}
	if err := models.CreateUser(u); err != nil {
		switch {
		case models.IsErrUserAlreadyExist(err):
			log.Errorf("username already taken")
			return fmt.Errorf("username already taken, sorry")
		case models.IsErrNameReserved(err):
			log.Errorf("username reserved")
			return fmt.Errorf("username reserved, please choose another username")
		case models.IsErrNamePatternNotAllowed(err):
			log.Errorf("invalid username pattern")
			return fmt.Errorf("invalid username pattern")
		default:
			log.Errorf("unknown error: %v", err)
			return fmt.Errorf("unknown error: %v", err)
		}
	}
	log.WithFields(log.Fields{
		"userID":   u.ID,
		"userName": u.UserName,
	}).Debugf("Account created")

	// Auto set Admin if first user
	if models.CountUsers() == 1 {
		u.Admin = models.BoolToFake(true)
		u.Active = models.BoolToFake(true) // bypass email activation
		if err := models.UpdateUser(u); err != nil {
			log.Errorf("cannot update user: %v", err)
			return fmt.Errorf("cannot update user: %v", err)
		}
	}

	return nil
}
