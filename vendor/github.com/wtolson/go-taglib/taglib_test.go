package taglib

import (
	"io"
	"io/ioutil"
	"os"
	"path"
	"strconv"
	"testing"
	"time"
)

func TestReadNothing(t *testing.T) {
	file, err := Read("doesnotexist.mp3")

	if file != nil {
		t.Fatal("Returned non nil file struct.")
	}

	if err == nil {
		t.Fatal("Returned nil err.")
	}

	if err != ErrInvalid {
		t.Fatal("Didn't return ErrInvalid")
	}
}

func TestReadDirectory(t *testing.T) {
	file, err := Read("/")

	if file != nil {
		t.Fatal("Returned non nil file struct.")
	}

	if err == nil {
		t.Fatal("Returned nil err.")
	}

	if err != ErrInvalid {
		t.Fatal("Didn't return ErrInvalid")
	}
}

func TestTagLib(t *testing.T) {
	file, err := Read("test.mp3")

	if err != nil {
		panic(err)
		t.Fatalf("Read returned error: %s", err)
	}

	defer file.Close()

	// Test the Tags
	if title := file.Title(); title != "The Title" {
		t.Errorf("Got wrong title: %s", title)
	}

	if artist := file.Artist(); artist != "The Artist" {
		t.Errorf("Got wrong artist: %s", artist)
	}

	if album := file.Album(); album != "The Album" {
		t.Errorf("Got wrong album: %s", album)
	}

	if comment := file.Comment(); comment != "A Comment" {
		t.Errorf("Got wrong comment: %s", comment)
	}

	if genre := file.Genre(); genre != "Booty Bass" {
		t.Errorf("Got wrong genre: %s", genre)
	}

	if year := file.Year(); year != 1942 {
		t.Errorf("Got wrong year: %d", year)
	}

	if track := file.Track(); track != 42 {
		t.Errorf("Got wrong track: %d", track)
	}

	// Test the properties
	if length := file.Length(); length != 42*time.Second {
		t.Errorf("Got wrong length: %s", length)
	}

	if bitrate := file.Bitrate(); bitrate != 128 {
		t.Errorf("Got wrong bitrate: %d", bitrate)
	}

	if samplerate := file.Samplerate(); samplerate != 44100 {
		t.Errorf("Got wrong samplerate: %d", samplerate)
	}

	if channels := file.Channels(); channels != 2 {
		t.Errorf("Got wrong channels: %d", channels)
	}
}

func TestWriteTagLib(t *testing.T) {
	fileName := "test.mp3"
	file, err := Read(fileName)

	if err != nil {
		panic(err)
		t.Fatalf("Read returned error: %s", err)
	}
	tempDir, err := ioutil.TempDir("", "go-taglib-test")

	if err != nil {
		panic(err)
		t.Fatalf("Cannot create temporary file for writing tests: %s", err)
	}

	tempFileName := path.Join(tempDir, "go-taglib-test.mp3")

	defer file.Close()
	defer os.RemoveAll(tempDir)

	err = cp(tempFileName, fileName)

	if err != nil {
		panic(err)
		t.Fatalf("Cannot copy file for writing tests: %s", err)
	}

	modifiedFile, err := Read(tempFileName)
	if err != nil {
		panic(err)
		t.Fatalf("Read returned error: %s", err)
	}
	modifiedFile.SetAlbum(getModifiedString(file.Album()))
	modifiedFile.SetComment(getModifiedString(file.Comment()))
	modifiedFile.SetGenre(getModifiedString(file.Genre()))
	modifiedFile.SetTrack(file.Track() + 1)
	modifiedFile.SetYear(file.Year() + 1)
	modifiedFile.SetArtist(getModifiedString(file.Artist()))
	modifiedFile.SetTitle(getModifiedString(file.Title()))
	err = modifiedFile.Save()
	if err != nil {
		panic(err)
		t.Fatalf("Cannot save file : %s", err)
	}
	modifiedFile.Close()
	//Re-open the modified file
	modifiedFile, err = Read(tempFileName)
	if err != nil {
		panic(err)
		t.Fatalf("Read returned error: %s", err)
	}

	// Test the Tags
	if title := modifiedFile.Title(); title != getModifiedString("The Title") {
		t.Errorf("Got wrong modified title: %s", title)
	}

	if artist := modifiedFile.Artist(); artist != getModifiedString("The Artist") {
		t.Errorf("Got wrong modified artist: %s", artist)
	}

	if album := modifiedFile.Album(); album != getModifiedString("The Album") {
		t.Errorf("Got wrong modified album: %s", album)
	}

	if comment := modifiedFile.Comment(); comment != getModifiedString("A Comment") {
		t.Errorf("Got wrong modified comment: %s", comment)
	}

	if genre := modifiedFile.Genre(); genre != getModifiedString("Booty Bass") {
		t.Errorf("Got wrong modified genre: %s", genre)
	}

	if year := modifiedFile.Year(); year != getModifiedInt(1942) {
		t.Errorf("Got wrong modified year: %d", year)
	}

	if track := modifiedFile.Track(); track != getModifiedInt(42) {
		t.Errorf("Got wrong modified track: %d", track)
	}
}

func TestGenericWriteTagLib(t *testing.T) {
	fileName := "test.mp3"
	file, err := Read(fileName)

	if err != nil {
		panic(err)
		t.Fatalf("Read returned error: %s", err)
	}
	tempDir, err := ioutil.TempDir("", "go-taglib-test")

	if err != nil {
		panic(err)
		t.Fatalf("Cannot create temporary file for writing tests: %s", err)
	}

	tempFileName := path.Join(tempDir, "go-taglib-test.mp3")

	defer file.Close()
	defer os.RemoveAll(tempDir)

	err = cp(tempFileName, fileName)

	if err != nil {
		panic(err)
		t.Fatalf("Cannot copy file for writing tests: %s", err)
	}

	modifiedFile, err := Read(tempFileName)
	if err != nil {
		panic(err)
		t.Fatalf("Read returned error: %s", err)
	}
	modifiedFile.SetTag(Album, getModifiedString(file.Album()))
	modifiedFile.SetTag(Comments, getModifiedString(file.Comment()))
	modifiedFile.SetTag(Genre, getModifiedString(file.Genre()))
	modifiedFile.SetTag(Track, strconv.Itoa(file.Track()+1))
	modifiedFile.SetTag(Year, strconv.Itoa(file.Year()+1))
	modifiedFile.SetTag(Artist, getModifiedString(file.Artist()))
	modifiedFile.SetTag(Title, getModifiedString(file.Title()))
	err = modifiedFile.Save()
	if err != nil {
		panic(err)
		t.Fatalf("Cannot save file : %s", err)
	}
	modifiedFile.Close()
	//Re-open the modified file
	modifiedFile, err = Read(tempFileName)
	if err != nil {
		panic(err)
		t.Fatalf("Read returned error: %s", err)
	}

	// Test the Tags
	if title := modifiedFile.Tag(Title); title != getModifiedString("The Title") {
		t.Errorf("Got wrong modified title: %s", title)
	}

	if artist := modifiedFile.Tag(Artist); artist != getModifiedString("The Artist") {
		t.Errorf("Got wrong modified artist: %s", artist)
	}

	if album := modifiedFile.Tag(Album); album != getModifiedString("The Album") {
		t.Errorf("Got wrong modified album: %s", album)
	}

	if comment := modifiedFile.Tag(Comments); comment != getModifiedString("A Comment") {
		t.Errorf("Got wrong modified comment: %s", comment)
	}

	if genre := modifiedFile.Tag(Genre); genre != getModifiedString("Booty Bass") {
		t.Errorf("Got wrong modified genre: %s", genre)
	}

	if year := modifiedFile.Tag(Year); year != strconv.Itoa(getModifiedInt((1942))) {
		t.Errorf("Got wrong modified year: %d", year)
	}

	if track := modifiedFile.Tag(Track); track != strconv.Itoa(getModifiedInt((42))) {
		t.Errorf("Got wrong modified track: %d", track)
	}
}

func checkModified(original string, modified string) bool {
	return modified == getModifiedString(original)
}

func getModifiedString(s string) string {
	return s + " MODIFIED"
}

func getModifiedInt(i int) int {
	return i + 1
}

func cp(dst, src string) error {
	s, err := os.Open(src)
	if err != nil {
		return err
	}
	// no need to check errors on read only file, we already got everything
	// we need from the filesystem, so nothing can go wrong now.
	defer s.Close()
	d, err := os.Create(dst)
	if err != nil {
		return err
	}
	if _, err := io.Copy(d, s); err != nil {
		d.Close()
		return err
	}
	return d.Close()
}
