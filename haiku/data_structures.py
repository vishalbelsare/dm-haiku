# Copyright 2019 DeepMind Technologies Limited. All Rights Reserved.
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
# ==============================================================================
# pylint: disable=g-importing-member
"""Public Haiku data structures."""

from haiku._src.data_structures import to_haiku_dict
from haiku._src.data_structures import to_immutable_dict
from haiku._src.data_structures import to_mutable_dict
from haiku._src.filtering import filter  # pylint: disable=redefined-builtin
from haiku._src.filtering import is_subset
from haiku._src.filtering import map  # pylint: disable=redefined-builtin
from haiku._src.filtering import merge
from haiku._src.filtering import partition
from haiku._src.filtering import partition_n
from haiku._src.filtering import traverse
from haiku._src.utils import tree_bytes
from haiku._src.utils import tree_size


__all__ = (
    "is_subset",
    "filter",
    "map",
    "merge",
    "partition",
    "partition_n",
    "to_haiku_dict",
    "to_mutable_dict",
    "to_immutable_dict",
    "traverse",
    "tree_bytes",
    "tree_size",
)
