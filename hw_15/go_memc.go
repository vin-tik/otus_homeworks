package main

import (
	"bufio"
	"compress/gzip"
	"errors"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/bradfitz/gomemcache/memcache"
	"github.com/golang/protobuf/proto"

	"./appsinstalled"
)

const NORMAL_ERR_RATE = 0.01

type AppsInstalled struct {
	dev_type string
	dev_id   string
	lat      float64
	lon      float64
	apps     []uint32
}
type Args struct {
	dry     bool
	pattern string
	idfa    string
	gaid    string
	adid    string
	dvid    string
}
type MemcacheItem struct {
	addr   string
	client *memcache.Client
}

func dotRename(path string) {
	head, fn := filepath.Split(path)

	err := os.Rename(path, filepath.Join(head, "."+fn))
	if err != nil {
		fmt.Println("Cannot rename file: %v", path)
	}
}

func insertAppsInstalled(memc, apps_installed *AppsInstalled, dryRun bool) bool {
	ua := &appsinstalled.UserApps{
		Lat:  proto.Float64(apps_installed.lat),
		Lon:  proto.Float64(apps_installed.lon),
		Apps: apps_installed.apps,
	}
	key := fmt.Sprintf("%v:%v", apps_installed.dev_type, apps_installed.dev_id)

	packed, err := proto.Marshal(ua)
	if err != nil {
		fmt.Println("Error: proto.Marshal")
	}

	if dryRun {
		fmt.Println("%v - %v -> %v", memc.addr, key, ua.String())
	} else {
		err := memc.client.Set(&memcache.Item{
			Key:   key,
			Value: packed,
		})
		if err != nil {
			fmt.Println("Cannot write to memc %v: %v", memc.addr, err)
			return false
		}
	}
	return true
}

func parseAppsInstalled(line string) (AppsInstalled, error) {
	var apps_installed AppsInstalled
	line_parts := strings.Split(line, "\t")

	if len(line_parts) < 5 {
		return apps_installed, errors.New("Invalid columns number")
	}

	dev_type := line_parts[0]
	dev_id := line_parts[1]
	if dev_type == "" || dev_id == "" {
		return apps_installed, errors.New("Invalid dev_type or dev_id")
	}

	var apps []uint32
	for _, appStr := range strings.Split(line_parts[4], ",") {
		app, _ := strconv.Atoi(appStr)
		apps = append(apps, uint32(app))
	}

	lat, latErr := strconv.ParseFloat(line_parts[2], 64)
	lon, lonErr := strconv.ParseFloat(line_parts[3], 64)
	if latErr != nil || lonErr != nil {
		fmt.Println("Invalid geo coords: `%v`", line)
	}

	apps_installed = AppsInstalled{
		dev_type: dev_type,
		dev_id:   dev_id,
		apps:     apps,
		lat:      lat,
		lon:      lon,
	}
	return apps_installed, nil
}

func log2memc(options *Args) {
	deviceMemc := map[string]string{
		"idfa": options.idfa,
		"gaid": options.gaid,
		"adid": options.adid,
		"dvid": options.dvid,
	}

	files, err := filepath.Glob(options.pattern)
	if err != nil {
		fmt.Println("No files for pattern `%v`", options.pattern)
		return
	}
	for _, fn := range files {
		processed, errors := 0, 0
		fmt.Println("Processing %v", fn)

		file, err := os.Open(fn)
		if err != nil {
			fmt.Println("Cannot read file: %v", err)
			return
		}
		defer file.Close()
		gz, err := gzip.NewReader(file)
		if err != nil {
			fmt.Println("Cannot open archive %v", err)
			return
		}
		defer gz.Close()

		scanner := bufio.NewScanner(gz)
		for scanner.Scan() {
			line := strings.TrimSpace(scanner.Text())
			if line == "" {
				continue
			}

			apps_installed, err := parseAppsInstalled(line)
			if err != nil {
				errors += 1
				continue
			}

			memc, found := deviceMemc[apps_installed.dev_type]
			if !found {
				errors += 1
				fmt.Println("Unknown device type: %v", apps_installed.dev_type)
				continue
			}

			ok := insertAppsInstalled(&memc, &apps_installed, options.dry)
			if ok {
				processed += 1
			} else {
				errors += 1
			}
		}
		if processed == 0 {
			dotRename(fn)
			continue
		}

		errRate := float64(errors) / float64(processed)
		if errRate < NORMAL_ERR_RATE {
			fmt.Println("Successfull load, err rate = %v", errRate)
		} else {
			fmt.Println("Too high error rate: (%v > %v). Loading failed", errRate, NORMAL_ERR_RATE)
		}
		dotRename(fn)
	}
}

func main() {
	dry := flag.Bool("dry", false, "")
	pattern := flag.String("pattern", "/data/appsinstalled/*.tsv.gz", "")
	logfile := flag.String("log", "", "")
	idfa := flag.String("idfa", "127.0.0.1:33013", "")
	gaid := flag.String("gaid", "127.0.0.1:33014", "")
	adid := flag.String("adid", "127.0.0.1:33015", "")
	dvid := flag.String("dvid", "127.0.0.1:33016", "")
	flag.Parse()

	options := &Args{
		dry:     dry,
		pattern: pattern,
		idfa:    idfa,
		gaid:    gaid,
		adid:    adid,
		dvid:    dvid,
	}

	if logfile != "" {
		f, err := os.OpenFile(logfile, os.O_WRONLY|os.O_CREATE|os.O_APPEND, 0644)
		if err != nil {
			fmt.Println("Cannot open log file: %s", logfile)
			return
		}
		defer f.Close()
		fmt.Println(f)
	}

	log2memc(options)
}
