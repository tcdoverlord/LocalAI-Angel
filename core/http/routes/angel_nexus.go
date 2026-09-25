package routes

import (
	"context"
	"io"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/labstack/echo/v4"
)

const (
	angelNexusPrefix      = "/api/angel-nexus"
	angelNexusInternalEnv = "ANGEL_NEXUS_INTERNAL_URL"
	angelNexusDefaultURL  = "http://nexus:8877"
	angelNexusTimeout     = 10 * time.Second
)

// RegisterAngelNexusRoutes exposes Angel Nexus through LocalAI's HTTP server.
// The browser talks only to LocalAI (/api/angel-nexus/*). LocalAI forwards the
// request over the internal Docker network to the Nexus service.
func RegisterAngelNexusRoutes(e *echo.Echo) {
	handler := angelNexusProxyHandler()
	e.Any(angelNexusPrefix, handler)
	e.Any(angelNexusPrefix+"/*", handler)
}

func angelNexusProxyHandler() echo.HandlerFunc {
	client := &http.Client{Timeout: angelNexusTimeout}

	return func(c echo.Context) error {
		path := c.Request().URL.Path
		relativePath := strings.TrimPrefix(path, angelNexusPrefix)
		if relativePath == "" {
			relativePath = "/"
		} else if !strings.HasPrefix(relativePath, "/") {
			relativePath = "/" + relativePath
		}

		baseURL := strings.TrimRight(os.Getenv(angelNexusInternalEnv), "/")
		if baseURL == "" {
			baseURL = angelNexusDefaultURL
		}

		targetURL := baseURL + relativePath
		if c.Request().URL.RawQuery != "" {
			targetURL += "?" + c.Request().URL.RawQuery
		}

		ctx, cancel := context.WithTimeout(c.Request().Context(), angelNexusTimeout)
		defer cancel()

		req, err := http.NewRequestWithContext(ctx, c.Request().Method, targetURL, c.Request().Body)
		if err != nil {
			return nexusProxyError(c, http.StatusBadGateway, "failed to create Angel Nexus request", err)
		}

		// Preserve the incoming request body's known length. NewRequestWithContext
		// cannot infer it from the incoming io.ReadCloser.
		req.ContentLength = c.Request().ContentLength

		copyRequestHeaders(req.Header, c.Request().Header)

		// Never let the browser-supplied Host header control the upstream target.
		req.Host = ""

		resp, err := client.Do(req)
		if err != nil {
			return nexusProxyError(c, http.StatusServiceUnavailable, "Angel Nexus service unavailable", err)
		}
		defer resp.Body.Close()

		copyResponseHeaders(c.Response().Header(), resp.Header)
		c.Response().WriteHeader(resp.StatusCode)
		_, copyErr := io.Copy(c.Response(), resp.Body)
		return copyErr
	}
}

func copyRequestHeaders(dst, src http.Header) {
	for key, values := range src {
		if isHopByHopHeader(key) {
			continue
		}
		for _, value := range values {
			dst.Add(key, value)
		}
	}
}

func copyResponseHeaders(dst, src http.Header) {
	for key, values := range src {
		if isHopByHopHeader(key) {
			continue
		}
		for _, value := range values {
			dst.Add(key, value)
		}
	}
}

func isHopByHopHeader(header string) bool {
	switch strings.ToLower(header) {
	case "connection",
		"keep-alive",
		"proxy-authenticate",
		"proxy-authorization",
		"te",
		"trailer",
		"transfer-encoding",
		"upgrade":
		return true
	default:
		return false
	}
}

func nexusProxyError(c echo.Context, status int, message string, cause error) error {
	if cause != nil {
		c.Logger().Errorf("Angel Nexus proxy: %s: %v", message, cause)
	}

	return c.JSON(status, map[string]string{
		"error":   message,
		"service": "angel-nexus",
	})
}
