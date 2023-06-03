# asciinema-scene

[![Release](https://img.shields.io/github/v/release/jdum/asciinema-scene)](https://img.shields.io/github/v/release/jdum/asciinema-scene)
[![Build status](https://img.shields.io/github/actions/workflow/status/jdum/asciinema-scene/main.yml?branch=main)](https://github.com/jdum/asciinema-scene/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/jdum/asciinema-scene/branch/main/graph/badge.svg)](https://codecov.io/gh/jdum/asciinema-scene)
[![Commit activity](https://img.shields.io/github/commit-activity/m/jdum/asciinema-scene)](https://img.shields.io/github/commit-activity/m/jdum/asciinema-scene)
[![License](https://img.shields.io/github/license/jdum/asciinema-scene)](https://img.shields.io/github/license/jdum/asciinema-scene)

`asciinema-scene` provides the `sciine` command line toolkit for editing screen casts produced by [asciinema](https://asciinema.org/).

`sciine` takes as input the content of a screencast, apply a unitary transformation and returns the transformed content.


## Installation

`asciinema-scene` is a python package:

``` bash
pip install asciinema-scene
```

## Usage


### Commandes


There are 3 types of commands:

- content information commands:
    - [status](#command-status)
    - [header](#command-header)
    - [show](#command-show)


- commands applying to a portion of the content:
    - [copy](#command-copy)
    - [cut](#command-cut)
    - [speed](#command-speed)
    - [minimum](#command-minimum)
    - [maximum](#command-maximum)
    - [quantize](#command-quantize)
    - [include](#command-include)


- command applying to a single frame:
    - [insert](#command-insert)
    - [replace](#command-replace)
    - [delete](#command-delete)


``` script
Usage: sciine [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  copy      Copy content between START and END timecodes.
  cut       Cut content between START and END timecodes.
  delete    Delete the frame with timecode >= TIMECODE.
  header    Print the header field of the content.
  include   Include the content of a .cast file at the timecode position.
  insert    Insert a frame at the TIMECODE position.
  maximum   Set maximum duration of each frame.
  minimum   Set minimum duration of each frame.
  quantize  Set the duration of frames in duration range to DURATION.
  replace   Replace the text of frame with timecode >= TIMECODE by TEXT.
  show      Print detail of frames, from START to END (max LINES).
  speed     Change the speed of the screen cast.
  status    Print informations about the content (duration, ...).
```

---

### Input / output

By default, `sciine` reads content from standard input and returns the result to standard output. The `--input` and `--output` options allow reading/writing from files (`sciine` can also read from a compressed `.zip` or `.gz` file). `sciine` does not modify the input file.

``` bash
-i, --input PATH   Input .cast file, default is stdin.
-o, --output PATH  Output .cast file, default is stdout.
```

Example:

Speed up a screencast and play a sub-part of it, using pipe redirection.


``` bash
sciine speed 2.0 --input short.cast | sciine copy --start 1.4 --end 2.4| asciinema play -
```

---

## Command `status`

``` script
Usage: sciine status [OPTIONS]

  Print informations about the content (duration, ...).

Options:
  -i, --input PATH  Input .cast file, default is stdin.
  --help            Show this message and exit.
```

Example:

Use `status` to see the number of frames and the duration of the screecast.


``` bash
sciine status --input short.cast
Input: short.cast
Date: 2023-05-28 11:15:06+00:00
Frames: 22
Duration: 6.135993
```

---

## Command `header`

``` script
Usage: sciine header [OPTIONS]

  Print the header field of the content.

Options:
  -i, --input PATH  Input .cast file, default is stdin.
  --help            Show this message and exit.
```

Example:

Display the original header.

``` bash
sciine header -i short.cast
{'env': {'SHELL': '/bin/bash', 'TERM': 'linux'},
 'height': 36,
 'timestamp': 1685272506,
 'version': 2,
 'width': 133}
```

---

## Command `show`

``` script
Usage: sciine show [OPTIONS]

  Print detail of frames, from START to END (max LINES).

  Each line prints the timecode, duration and text of the frame. If no START
  timecode is provided, start from the beginning. If no END timecode is
  provided, display all lines until the end, or LINES lines

Options:
  -s, --start FLOAT    Start timecode (sec), default is 0.0.
  -e, --end FLOAT      End timecode (sec), default is EOF.
  -l, --lines INTEGER  Number of lines to show.
  -p, --precise        Show all digits of time codes.
  -t, --text           Show message field as plain text.
  -i, --input PATH     Input .cast file, default is stdin.
  --help               Show this message and exit.
```

Example:

Display the first 5 lines and the precise duration of the frames.

``` bash
sciine show --lines 5 --precise  -i short.cast
  0.000000│ 0.894038│ 'e'
  0.894038│ 0.104510│ 'c'
  0.998548│ 0.164761│ 'h'
  1.163309│ 0.300601│ 'o'
  1.463910│ 0.392259│ ' '
```

---

## Command `copy`

``` script
Usage: sciine copy [OPTIONS]

  Copy content between START and END timecodes.

Options:
  -s, --start FLOAT  Start timecode (sec), default is 0.0.
  -e, --end FLOAT    End timecode (sec), default is EOF.
  -i, --input PATH   Input .cast file, default is stdin.
  -o, --output PATH  Output .cast file, default is stdout.
  --help             Show this message and exit.
```

Example:

Play content between 0.05 and 1.2 seconds.

``` bash
sciine copy --start 0.05 --end 1.2 -i short.cast | asciinema play -
```

---

## Command `cut`

``` script
Usage: sciine cut [OPTIONS]

  Cut content between START and END timecodes.

  If no START timecode is provided, cut from the beginning. If no END timecode
  is provided, cut until the end.

Options:
  -s, --start FLOAT  Start timecode (sec), default is 0.0.
  -e, --end FLOAT    End timecode (sec), default is EOF.
  -a, --adjust       Adjust durations of frames at precise cut values.
  -i, --input PATH   Input .cast file, default is stdin.
  -o, --output PATH  Output .cast file, default is stdout.
  --help             Show this message and exit.
```

Example:

Cut end of content after 1.2 seconds.

``` bash
sciine cut --start 1.2 < short.cast | asciinema play -
```

---

## Command `speed`

``` script
Usage: sciine speed [OPTIONS] SPEED

  Change the speed of the screen cast.

  SPEED is the factor of acceleration. Use number below 1.0 to to slow down.
  If no START timecode is provided, modify speed from the beginning. If no END
  timecode is provided, modify speed until the end.

Options:
  -s, --start FLOAT  Start timecode (sec), default is 0.0.
  -e, --end FLOAT    End timecode (sec), default is EOF.
  -i, --input PATH   Input .cast file, default is stdin.
  -o, --output PATH  Output .cast file, default is stdout.
  --help             Show this message and exit.
```

Example:

Doubles the speed and displays the new duration.

``` bash
sciine speed 2.0 -i short.cast|sciine status
Input: sys.stdin
Date: 2023-06-03 11:10:23+00:00
Frames: 22
Duration: 3.067996
```

---

## Command `minimum`

``` script
Usage: sciine minimum [OPTIONS] DURATION

  Set minimum duration of each frame.

  The minimum duration of frames will be set to DURATION seconds, the
  timecodes will be adjusted accordingly. If no START timecode is provided,
  apply from the beginning. If no END timecode is provided, apply until the
  end.

Options:
  -s, --start FLOAT  Start timecode (sec), default is 0.0.
  -e, --end FLOAT    End timecode (sec), default is EOF.
  -i, --input PATH   Input .cast file, default is stdin.
  -o, --output PATH  Output .cast file, default is stdout.
  --help             Show this message and exit.
```

Example:

Set the frame duration to a minimum of 0.2s and display the new durations.

``` bash
sciine minimum 0.2 -i short.cast | sciine show -l 5 -p
  0.000000│ 0.894038│ 'e'
  0.894038│ 0.200000│ 'c'
  1.094038│ 0.200000│ 'h'
  1.294038│ 0.300601│ 'o'
  1.594639│ 0.392259│ ' '
```

---

## Command `maximum`

``` script
Usage: sciine maximum [OPTIONS] DURATION

  Set maximum duration of each frame.

  The duration of frames will be limited to DURATION seconds, the timecodes
  will be adjusted accordingly. If no START timecode is provided, apply from
  the beginning. If no END timecode is provided, apply until the end.

Options:
  -s, --start FLOAT  Start timecode (sec), default is 0.0.
  -e, --end FLOAT    End timecode (sec), default is EOF.
  -i, --input PATH   Input .cast file, default is stdin.
  -o, --output PATH  Output .cast file, default is stdout.
  --help             Show this message and exit.
```

Example:

Set the frame duration to a maximum of 0.2s and display the new durations.

``` bash
sciine maximum 0.2 -i short.cast | sciine show -l 5 -p
  0.000000│ 0.200000│ 'e'
  0.200000│ 0.104510│ 'c'
  0.304510│ 0.164761│ 'h'
  0.469271│ 0.200000│ 'o'
  0.669271│ 0.200000│ ' '
```

---

## Command `quantize`

``` script
Usage: sciine quantize [OPTIONS] RANGE_MIN RANGE_MAX DURATION

  Set the duration of frames in duration range to DURATION.

  Set the duration of frames to DURATION if their current duration is between
  RANGE_MIN and RANGE_MAX. If no START timecode is provided, apply from the
  beginning. If no END timecode is provided, apply until the end.

Options:
  -s, --start FLOAT  Start timecode (sec), default is 0.0.
  -e, --end FLOAT    End timecode (sec), default is EOF.
  -i, --input PATH   Input .cast file, default is stdin.
  -o, --output PATH  Output .cast file, default is stdout.
  --help             Show this message and exit.
```

Example:

Set the frame duration to 0.2s for all frames lasting between 0.1 and 0.4s.

``` bash
sciine quantize 0.1 0.4 0.2 -i short.cast | sciine show -l 5 -p
  0.000000│ 0.894038│ 'e'
  0.894038│ 0.200000│ 'c'
  1.094038│ 0.200000│ 'h'
  1.294038│ 0.200000│ 'o'
  1.494038│ 0.200000│ ' '
```

---

## Command `include`

``` script
Usage: sciine include [OPTIONS] TIMECODE INCLUDE_FILE

  Include the content of a .cast file at the timecode position.

  All frames of the INCLUDE_FILE .cast file will be copied in the current
  screen cast. The timecodes will be adjusted as required.

Options:
  -i, --input PATH   Input .cast file, default is stdin.
  -o, --output PATH  Output .cast file, default is stdout.
  --help             Show this message and exit.
```

Add the content of `long.cast` to the beginning of the screencast, and display the final duration.

``` bash
sciine include 0.0 long.cast.gz  -i short.cast|sciine status
Input: sys.stdin
Date: 2023-06-03 12:14:22+00:00
Frames: 71391
Duration: 22.925312
```

---

## Command `insert`

``` script
Usage: sciine insert [OPTIONS] TIMECODE DURATION TEXT [ETYPE]

  Insert a frame at the TIMECODE position.

  The frame will display TEXT during DURATION seconds. By default the event
  type ETYPE is set to "o".

Options:
  -i, --input PATH   Input .cast file, default is stdin.
  -o, --output PATH  Output .cast file, default is stdout.
  --help             Show this message and exit.
```

Insert the string 'xyz' at position 2.0 for a duration of 0.1s. View content before and after the change.

``` bash
sciine show -l 8 -p -i short.cast
  0.000000│ 0.894038│ 'e'
  0.894038│ 0.104510│ 'c'
  0.998548│ 0.164761│ 'h'
  1.163309│ 0.300601│ 'o'
  1.463910│ 0.392259│ ' '
  1.856169│ 0.356967│ '"'
  2.213136│ 0.150277│ 'a'
  2.363413│ 0.511288│ ' '

sciine insert 2.0 0.1 "xyz" -i short.cast | sciine show -l 8 -p
  0.000000│ 0.894038│ 'e'
  0.894038│ 0.104510│ 'c'
  0.998548│ 0.164761│ 'h'
  1.163309│ 0.300601│ 'o'
  1.463910│ 0.392259│ ' '
  1.856169│ 0.356967│ '"'
  2.213136│ 0.100000│ 'xyz'
  2.313136│ 0.150277│ 'a'
```

---

## Command `replace`

``` script
Usage: sciine replace [OPTIONS] TIMECODE TEXT

  Replace the text of frame with timecode >= TIMECODE by TEXT.

Options:
  -i, --input PATH   Input .cast file, default is stdin.
  -o, --output PATH  Output .cast file, default is stdout.
  --help             Show this message and exit.
```

Replace the string 'xyz' at position 2.0 for a duration of 0.1s. View content before and after the change.

``` bash
sciine show -l 8 -p -i short.cast
  0.000000│ 0.894038│ 'e'
  0.894038│ 0.104510│ 'c'
  0.998548│ 0.164761│ 'h'
  1.163309│ 0.300601│ 'o'
  1.463910│ 0.392259│ ' '
  1.856169│ 0.356967│ '"'
  2.213136│ 0.150277│ 'a'
  2.363413│ 0.511288│ ' '

sciine replace 2.0 "xyz" -i short.cast | sciine show -l 8 -p
  0.000000│ 0.894038│ 'e'
  0.894038│ 0.104510│ 'c'
  0.998548│ 0.164761│ 'h'
  1.163309│ 0.300601│ 'o'
  1.463910│ 0.392259│ ' '
  1.856169│ 0.356967│ '"'
  2.213136│ 0.150277│ 'xyz'
  2.363413│ 0.511288│ ' '
```

---

## Command `delete`

``` script
Usage: sciine delete [OPTIONS] TIMECODE

  Delete the frame with timecode >= TIMECODE.

Options:
  -i, --input PATH   Input .cast file, default is stdin.
  -o, --output PATH  Output .cast file, default is stdout.
  --help             Show this message and exit.
```

Delete the frame at position 2.0. View content before and after the change.

``` bash
sciine show -l 8 -p -i short.cast
  0.000000│ 0.894038│ 'e'
  0.894038│ 0.104510│ 'c'
  0.998548│ 0.164761│ 'h'
  1.163309│ 0.300601│ 'o'
  1.463910│ 0.392259│ ' '
  1.856169│ 0.356967│ '"'
  2.213136│ 0.150277│ 'a'
  2.363413│ 0.511288│ ' '

sciine delete 2.0  -i short.cast | sciine show -l 8 -p
  0.000000│ 0.894038│ 'e'
  0.894038│ 0.104510│ 'c'
  0.998548│ 0.164761│ 'h'
  1.163309│ 0.300601│ 'o'
  1.463910│ 0.392259│ ' '
  1.856169│ 0.356967│ '"'
  2.213136│ 0.511288│ ' '
  2.724424│ 0.237965│ 's'
```

---

## Code source

**Github repository**: <https://github.com/jdum/asciinema-scene/>

## License

This project is licensed under the MIT License (see the LICENSE file for details).
