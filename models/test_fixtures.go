package models

import (
	"github.com/go-testfixtures/testfixtures"
	log "github.com/sirupsen/logrus"
)

var fixtures *testfixtures.Context

// InitFixtures initialize test fixtures for a test database
func InitFixtures(helper testfixtures.Helper, dir string) (err error) {
	testfixtures.SkipDatabaseNameCheck(true)
	fixtures, err = testfixtures.NewFolder(db.DB(), helper, dir)
	return err
}

// LoadFixtures load fixtures for a test database
func LoadFixtures() error {
	db.AutoMigrate(&User{}, &Album{}, &Track{}, &TrackInfo{}, &TimelineItem{})
	err := fixtures.Load()
	if err != nil {
		log.Errorf("Error loading fixtures: %v", err)
	}
	return err
}
