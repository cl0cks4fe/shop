package ui

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"os"
	"time"
)

// GadgetAddress returns the target gadget server URL.
func GadgetAddress() string {
	if addr := os.Getenv("GADGET_URL"); addr != "" {
		return addr
	}
	return "http://localhost:3000"
}

// GadgetStatus holds the response from /ping.
type GadgetStatus struct {
	Online         bool
	DeviceName     string `json:"device_name"`
	TransferActive bool   `json:"transfer_active"`
	ActiveTransfer string `json:"active_transfer"`
}

// PingGadget hits /ping and returns the gadget's current status.
func PingGadget(addr string) GadgetStatus {
	client := &http.Client{Timeout: 2 * time.Second}
	resp, err := client.Get(addr + "/ping")
	if err != nil {
		return GadgetStatus{}
	}
	defer resp.Body.Close()
	var s GadgetStatus
	if err := json.NewDecoder(resp.Body).Decode(&s); err != nil {
		return GadgetStatus{}
	}
	s.Online = true
	return s
}

// SendToGadget uploads a file to the gadget's /upload endpoint.
func SendToGadget(addr, filename string, data []byte) error {
	body := &bytes.Buffer{}
	w := multipart.NewWriter(body)

	part, err := w.CreateFormFile("file", filename)
	if err != nil {
		return fmt.Errorf("create form: %w", err)
	}
	if _, err := io.Copy(part, bytes.NewReader(data)); err != nil {
		return fmt.Errorf("write data: %w", err)
	}
	w.Close()

	resp, err := http.Post(addr+"/upload", w.FormDataContentType(), body)
	if err != nil {
		return fmt.Errorf("upload failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 400 {
		return fmt.Errorf("gadget returned HTTP %d", resp.StatusCode)
	}
	return nil
}
