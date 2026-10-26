# Canned gh responses

The runner returns these when the matching read-only `gh` command is run against `acme-billing/invoicesvc`. Anything not listed returns `HTTP 404: Not Found`.

| Command (shape) | Result |
|---|---|
| `gh auth status` | Logged in to github.com, token scopes: `repo:read` (fine-grained, Contents: read) |
| `gh api repos/acme-billing/invoicesvc --jq .default_branch` | `main` |
| `gh api repos/acme-billing/invoicesvc/commits/v3.8.2 --jq .sha` | `5f2c9a1e7b3d4c6a8e0f1b2d3c4e5f6a7b8c9d0e` |
| `gh api repos/acme-billing/invoicesvc/commits/main --jq .sha` | `9b81d0c2…` (3 commits ahead of `v3.8.2`) |
| `gh api "repos/acme-billing/invoicesvc/git/trees/<v3.8.2 sha>?recursive=1" --jq '.tree[].path'` | `README.md`, `go.mod`, `cmd/invoicesvc/main.go`, `internal/config/config.go`, `internal/render/pdf.go`, `internal/store/s3.go`, `Dockerfile` |
| contents of `internal/config/config.go` at `v3.8.2` | see block A |
| contents of `internal/store/s3.go` at `v3.8.2` | see block B |
| contents of `cmd/invoicesvc/main.go` at `v3.8.2` | see block C |
| contents of `internal/render/pdf.go` at `v3.8.2` | `package render` … uses `cfg.PDFTimeout` as a `context.WithTimeout` deadline; no env reads |
| `gh search code ... repo:acme-billing/invoicesvc` (any query) | results come from the default branch `main` only |
| `gh api repos/acme-billing/invoicesvc/contents/... ?ref=main` (any file) | same as `v3.8.2` for the files above |

## Block A — `internal/config/config.go`

```go
 1  package config
 2
 3  import (
 4  	"log"
 5  	"os"
 6  	"time"
 7  )
 8
 9  type Config struct {
10  	Port       string
11  	Bucket     string
12  	PDFTimeout time.Duration
13  }
14
15  func Load() Config {
16  	c := Config{Port: getenv("HTTP_PORT", "8080")}
17  	c.Bucket = os.Getenv("INVOICE_BUCKET")
18  	d, err := time.ParseDuration(getenv("PDF_TIMEOUT", "5s"))
19  	if err != nil {
20  		log.Printf("bad PDF_TIMEOUT, using 5s: %v", err)
21  		d = 5 * time.Second
22  	}
23  	c.PDFTimeout = d
24  	return c
25  }
26
27  func getenv(k, def string) string {
28  	if v := os.Getenv(k); v != "" {
29  		return v
30  	}
31  	return def
32  }
```

## Block B — `internal/store/s3.go`

```go
 1  package store
 2
 3  // Save uploads a rendered invoice. An empty bucket name makes every
 4  // PutObject fail with InvalidBucketName / MissingParameter.
 5  func (s *Store) Save(ctx context.Context, key string, pdf []byte) error {
 6  	_, err := s.s3.PutObject(ctx, &s3.PutObjectInput{
 7  		Bucket: aws.String(s.bucket),
 8  		Key:    aws.String(key),
 9  		Body:   bytes.NewReader(pdf),
10  	})
11  	return err
12  }
```

## Block C — `cmd/invoicesvc/main.go` (excerpt)

```go
14  func main() {
15  	cfg := config.Load()
16  	st := store.New(cfg.Bucket)
17  	http.HandleFunc("/healthz", func(w http.ResponseWriter, _ *http.Request) { w.WriteHeader(200) })
18  	http.HandleFunc("/invoices", invoiceHandler(st, cfg))
19  	log.Fatal(http.ListenAndServe(":"+cfg.Port, nil))
20  }
```
