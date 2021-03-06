#!/bin/bash
#
# Copyright 2017 Istio Authors
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

set -o errexit

VERSION="v1"

SCRIPTDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

pushd $SCRIPTDIR/productpage-prod
  docker build -t openpolicyagent/demo-bookinfo-productpage-v1:${VERSION} .
popd

pushd $SCRIPTDIR/details
  docker build -t openpolicyagent/demo-bookinfo-details-v1:${VERSION} .
popd

pushd $SCRIPTDIR/reviews
  #java build the app.
  docker run --rm -u root -v `pwd`:/usr/bin/app:rw -w /usr/bin/app gradle:4.8.1 gradle clean build
  pushd reviews-wlpcfg
    #with ratings black stars
    docker build -t openpolicyagent/demo-bookinfo-reviews-v2:${VERSION} --build-arg service_version=v2 --build-arg enable_ratings=true .
  popd
popd

pushd $SCRIPTDIR/ratings
  docker build -t openpolicyagent/demo-bookinfo-ratings-v1:${VERSION} --build-arg service_version=v1 .
  docker build -t openpolicyagent/demo-bookinfo-ratings-v2:${VERSION} --build-arg service_version=v2 .
popd

pushd $SCRIPTDIR/mysql
  docker build -t openpolicyagent/demo-bookinfo-mysqldb:${VERSION} .
popd

pushd $SCRIPTDIR/mongodb
  docker build -t openpolicyagent/demo-bookinfo-mongodb:${VERSION} .
popd
