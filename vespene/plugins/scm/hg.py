#  Copyright 2018, Michael DeHaan LLC
#  Copyright 2018, Jon Hawkesworth figs@unity.demon.co.uk
#  License: Apache License Version 2.0
#  -------------------------------------------------------------------------
#  hg.py - code for working with mercurial.
#  At the time of writing, mercurial is still python 2 dependent, so
#  to avoid surprises when mercurial starts running under python 3,
#  this just runs mercurial as if at the command line.
#  --------------------------------------------------------------------------

import os
import shlex

from vespene.common.logger import Logger
from vespene.workers import commands

LOG = Logger()

class Plugin(object):

    def __init__(self):
        pass

    def setup(self, build):
        # Basic constructor, takes a build
        self.build = build
        self.project = build.project
        self.repo = build.project.repo_url

    def get_revision(self):
        # Implementation of revision lookup for hg
        cmd = "(cd %s; hg identify -i)" % self.build.working_dir
        out = commands.execute_command(self.build, cmd, output_log=False, message_log=True)
        return out.split("\n")[0].strip()

    def get_last_commit_user(self):
        # Implementation of last commit user lookup for hg
        cmd = "(cd %s; hg log -l1 -T '{desc} (#{p1rev})\n')" % (self.build.working_dir)
        out = commands.execute_command(self.build, cmd, output_log=False, message_log=True)
        return out.split("\n")[0].strip()

    def checkout(self):
        # HG checkout implementation.
        self.build.append_message("----------\nCloning repository...")

        # TODO: support ssh:// sources
        clone_config = ""
        key_mgmt = dict()

        # use ~/.hgrc if present and readable
        if os.path.isfile("~/.hgrc") and os.access("~/.hgrc", os.R_OK):
           self.build.append_message("Using credentials from ~/.hgrc")
        else:
           if self.repo.startswith("http://") or self.repo.startswith("https://"):
               if self.project.scm_login and self.project.scm_login.password is not None:
                   # Its possible using 'prefix=*' like this wont work, especially
                   # if the user you are cloning as has an existing .hgrc
                   # See 'auth' 'prefix' here: https://www.selenic.com/mercurial/hgrc.5.html
                   # but tldr; is that the longest prefix wins and * is considered to have a length of 1
                   # So the assumption is the user who is cloning does _not_ have
                   # an ~/.hgrc/ with an [auth] section containing any prefixes
                   clone_config = " --config 'auth.vespene.prefix=*' --config 'auth.vespene.username=%s' --config 'auth.vespene.password=%s'" % (self.project.scm_login.username, self.project.scm_login.get_password())
           elif self.repo.startswith("ssh://"):
                self.build.append_message("Using ssh for user '%s'" % (self.project_scm_login))
           else:
               raise Exception("%s is not a supported mercurial source.   Please use a source begining ssh:// http:// or https://" % (self.repo))

        branch_spec = ""
        if self.project.repo_branch:
            branch_spec = "-b %s " % shlex.quote(self.project.repo_branch)

        try:
            # run it
            cmd = "hg clone %s%s %s %s" % (branch_spec, shlex.quote(self.repo), self.build.working_dir, clone_config)
            # TODO modify to have watch phrases that kill the command automatically when we see certain output.
            output = commands.execute_command(self.build, cmd, output_log=False, message_log=True, timeout=600, env=key_mgmt)
        finally:
            self.build.append_message("\nClone step completed\n")
        return output
