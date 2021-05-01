#!/usr/bin/python3

import yaml
import subprocess
import os


def get_available_targets():
	res = subprocess.run(["make", "list-targets"], stdout=subprocess.PIPE)
	return res.stdout.decode('utf-8').strip().split("\n")

BEFORE_SCRIPT = [
	"apt-get update > /dev/null",
	"apt-get install -y curl git libncurses-dev build-essential make gawk unzip wget python2.7 file tar bzip2 > /dev/null",
]

ci = {
	"image": "debian:stable",
	"stages": [
		"build",
		"deploy"
	],
	"build-all": {
		"stage": "build",
		"before_script": BEFORE_SCRIPT,
		"parallel": {
			"matrix": [
				{"TARGET": get_available_targets()}
			]
		},
		"script": [
			"git clone -q https://github.com/freifunk-gluon/gluon.git",
			"cd gluon",
			"git clone  ../ site",
			"./site/ci-build-images.sh",
		],
		"artifacts": {
			"when": "always",
			"paths": ["gluon/output"]
		}

	}
}

deploy = yaml.full_load("""\
stage: deploy
before_script:
- apt-get -qq update
- apt-get -qq install -y git make gawk wget python2.7 file tar bzip2 rsync
script:
- mkdir -p ~/.ssh
- 'echo -e "StrictHostKeyChecking no" > ~/.ssh/config'
- eval $(ssh-agent -s)
- echo "$DEPLOY_KEY" | ssh-add -
- DATE=$(date +%F-%H-%M-%S)
- mkdir -p "public/$DATE"
- cd gluon
- mv output $DATE
- ln -s "./$DATE" ./latest
- find "$DATE" -maxdepth 2
- rsync -rvhl "./$DATE" "${DEPLOY_USER}@${DEPLOY_HOST}:data/"
- rsync -rvhl ./latest "${DEPLOY_USER}@${DEPLOY_HOST}:data/"
"""
)

ci['upload'] = deploy

print(yaml.dump(ci, sort_keys=False))
# print(get_available_targets())
