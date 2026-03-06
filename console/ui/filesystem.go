package ui

import (
	"os"
	"path/filepath"
	"strings"
)

// FileEntry represents a single file or folder on disk.
type FileEntry struct {
	Path     string
	Name     string
	Size     int64
	IsFolder bool
}

// FileSystem browses a root directory (e.g. a Google Drive sync folder).
type FileSystem struct {
	root string
}

// NewFileSystem finds the local Google Drive sync folder and returns a browser.
func NewFileSystem() (*FileSystem, error) {
	home, err := os.UserHomeDir()
	if err != nil {
		return nil, err
	}
	root := filepath.Join(home, "drive")
	return &FileSystem{root: root}, nil
}

func (fs *FileSystem) Root() string {
	return fs.root
}

func (fs *FileSystem) RootName() string {
	return filepath.Base(fs.Root())
}

// List returns the contents of a directory. Pass "" for the root.
func (fs *FileSystem) List(dir string) ([]FileEntry, error) {
	if dir == "" {
		dir = fs.root
	}

	entries, err := os.ReadDir(dir)
	if err != nil {
		return nil, err
	}

	out := make([]FileEntry, 0, len(entries))
	for _, e := range entries {
		if strings.HasPrefix(e.Name(), ".") {
			continue
		}
		info, err := e.Info()
		if err != nil {
			continue
		}
		out = append(out, FileEntry{
			Path:     filepath.Join(dir, e.Name()),
			Name:     e.Name(),
			Size:     info.Size(),
			IsFolder: e.IsDir(),
		})
	}
	return out, nil
}

// ReadFile returns the raw bytes of a file by its full path.
func (fs *FileSystem) ReadFile(path string) ([]byte, error) {
	return os.ReadFile(path)
}
