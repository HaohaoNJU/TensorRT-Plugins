#
# Copyright (c) 2021, NVIDIA CORPORATION. All rights reserved.
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
#
from polygraphy import util
from polygraphy.common import TensorMetadata
from polygraphy.comparator import RunResults
from polygraphy.comparator import util as comp_util
from polygraphy.json import load_json
from polygraphy.logger import G_LOGGER
from polygraphy.tools.base import Tool


class Data(Tool):
    """
    Display information about inference inputs and outputs saved from Polygraphy's Comparator.run()
    (for example, outputs saved by `--save-outputs` or inputs saved by `--save-inputs` from `polygraphy run`).
    """

    def __init__(self):
        super().__init__("data")

    def add_parser_args(self, parser):
        parser.add_argument("path", help="Path to a file containing input or output data from Polygraphy")
        parser.add_argument(
            "-a",
            "--all",
            help="Show information on all iterations present in the data instead of just the first",
            action="store_true",
        )
        parser.add_argument(
            "-s", "--show-values", help="Show values of the tensors instead of just metadata", action="store_true"
        )
        parser.add_argument("--histogram", help="Show a histogram of the value distribution", action="store_true")

    def run(self, args):
        # Note: It's important we have encode/decode JSON methods registered
        # for the types we care about, e.g. RunResults. Importing the class should generally guarantee this.
        data = load_json(args.path)

        def meta_from_iter_result(iter_result):
            meta = TensorMetadata()
            for name, arr in iter_result.items():
                meta.add(name, dtype=arr.dtype, shape=arr.shape)
            return meta

        def str_from_iters(iters):
            out_str = ""
            for index, iter_result in enumerate(iters):
                iter_meta = meta_from_iter_result(iter_result)
                if len(iters) > 1 and args.all:
                    out_str += util.indent_block("Iteration: {:} | ".format(index))

                for name, arr in iter_result.items():
                    out_str += "\n{:} {:} | Stats\n".format(name, iter_meta[name])
                    out_str += util.indent_block(comp_util.str_output_stats(arr)) + "\n"
                    if args.histogram:
                        out_str += util.indent_block(comp_util.str_histogram(arr)) + "\n"
                    if args.show_values:
                        out_str += "{:}\n".format(util.indent_block(str(arr)))

                if not args.all:
                    break
            return out_str

        def display_results(results):
            results_str = ""
            results_str += "==== Run Results ({:} runners) ====\n\n".format(len(results))

            max_runner_width = max(len(runner_name) for runner_name in results.keys())
            for runner_name, iters in results.items():
                results_str += "---- {:<{max_runner_width}} ({:} iterations) ----\n".format(
                    runner_name, len(iters), max_runner_width=max_runner_width
                )
                results_str += str_from_iters(iters) + "\n"

            results_str = util.indent_block(results_str, level=0).strip()
            G_LOGGER.info(results_str)

        def display_inputs(input_data):
            inputs_str = ""
            inputs_str += "==== Data ({:} iterations) ====\n".format(len(input_data))
            inputs_str += str_from_iters(input_data) + "\n"
            inputs_str = util.indent_block(inputs_str, level=0).strip()
            G_LOGGER.info(inputs_str)

        if isinstance(data, RunResults):
            display_results(data)
        else:
            if not util.is_sequence(data):
                data = [data]
            display_inputs(data)
