# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""This script is used to synthesize generated parts of this library."""

import os
from pathlib import Path
import tempfile
from typing import Union

import synthtool as s
from synthtool.languages import java
from synthtool.sources import git
from synthtool import logger, shell

GOOGLEAPIS_URL = git.make_repo_clone_url("googleapis/googleapis")

logger.debug("Cloning googleapis.")
googleapis = git.clone(GOOGLEAPIS_URL)

def bazel_build(target: str, cwd: Union[Path, str]) -> Path:
  """Build a bazel target and return the output build directory."""
  old_cwd = os.getcwd()
  os.chdir(str(cwd))

  bazel_run_args = [
      "bazel",
      "--max_idle_secs=240",
      "build",
      target,
  ]

  logger.debug(f"Generating code for: {target}.")
  shell.run(bazel_run_args)

  output_dir = Path(f"bazel-bin{os.path.sep}{target[2:].split(':')[0]}").resolve()
  os.chdir(old_cwd)

  return output_dir

def build_proto(target):
  """Build a proto build target and copy all generate source files."""
  output = bazel_build(
      target=target,
      cwd=googleapis,
  )

  src_output = Path(tempfile.mkdtemp())
  for proto_jar in output.glob("*-speed-src.jar"):
    logger.debug(f"unzipping: {os.path.basename(proto_jar)}")
    shell.run(["unzip", "-o", proto_jar, "-d", src_output / "src"])

  java.fix_proto_headers(src_output)
  s.copy(src_output / "src/com", "proto-google-apps-script-type-protos/src/main/java/com")

build_proto("//google/apps/script/type:type_java_proto")
build_proto("//google/apps/script/type/calendar:calendar_java_proto")
build_proto("//google/apps/script/type/docs:docs_java_proto")
build_proto("//google/apps/script/type/drive:drive_java_proto")
build_proto("//google/apps/script/type/gmail:gmail_java_proto")
build_proto("//google/apps/script/type/sheets:sheets_java_proto")
build_proto("//google/apps/script/type/slides:slides_java_proto")

java.format_code("proto-google-apps-script-type-protos/src")
