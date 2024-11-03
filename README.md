## Getting Started

Current version that works: Branch `python-gui`

### Prerequisites

install the following:

- flask
- gstreamer
- gst-plugins-good
- gst-plugins-base
- opus
  (i installed these using homebrew)

```
brew install gstreamer gst-plugins-good gst-plugins-base opus
```

add the following to your .bashrc or .zshrc

```
export DYLD_LIBRARY_PATH=$(brew --prefix)/lib/gstreamer-1.0
```

```
export GST_PLUGIN_PATH=$(brew --prefix)/lib/gstreamer-1.0
```

### Installing

1. Clone the repository

(sadly this was done in my base env, so ignore the `requirements.txt` file)
