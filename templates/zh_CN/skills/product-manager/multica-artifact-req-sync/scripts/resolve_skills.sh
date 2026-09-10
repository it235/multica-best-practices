#!/bin/bash
# Resolve platform skill directories — delegates to templates/skills/_lib
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../../（按 skill 名）.sh
source "$SCRIPT_DIR/../../../（按 skill 名）.sh"
