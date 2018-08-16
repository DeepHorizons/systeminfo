import subprocess
import logging
import json
import re
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Information:
    """
    This class represents a single system and you can query it to get that
    information.
    """
    def __init__(self, pre_command='', timeout=30):
        """
        pre_command: The string to put in front of any command run. Useful for running remote commands
        timeout: The maximum time a command should take
        """
        self.pre_command = pre_command
        self.timeout = timeout
        self.stderr_into_stdout = True

    @property
    def log(self):
        return logger

    def process_command(self, command):
        # TODO handle list as well for when shell != True
        if type(command) is list:
            if type(self.pre_command is not list):
                cmd = self.pre_command.split() + command
            else:
                cmd = self.pre_command + command
        else:
            if type(self.pre_command) is list:
                cmd = ' '.join(self.pre_command) + command
            else:
                cmd = self.pre_command + command
        return cmd

    def run_command(self, command, shell=False):
        cmd = self.process_command(command)
        self.log.debug('Running: `{cmd}`'.format(cmd=cmd))
        stderr = subprocess.STDOUT if self.stderr_into_stdout else subprocess.DEVNULL
        status = subprocess.run(cmd, shell=shell, timeout=self.timeout, stdout=subprocess.PIPE, stderr=stderr)
        return status
    
    async def async_run_command(self, command):
        cmd = self.process_command(command)
        self.log.debug('Running: `{cmd}`'.format(cmd=cmd))
        stderr = asyncio.subprocess.STDOUT if self.stderr_into_stdout else asyncio.subprocess.DEVNULL
        status = await asyncio.subprocess.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=stderr)
        return status
    
    def get_command_text(self, command, shell=False, check=True):
        status = self.run_command(command, shell)
        if check:
            status.check_returncode()
        text = status.stdout.decode('utf-8')
        self.log.debug('cmd output: `{text}`'.format(text=text))
        return text
    
    async def async_get_command_text(self, command, check=True):
        status = await self.async_run_command(command)
        # I think we want to use communicate first, so we get the text, then call wait to set returncode
        # TODO does communicate() set the returncode?
        stdout, stderr = await asyncio.wait_for(status.communicate(), self.timeout)  # You wait for the timeout
        await status.wait()  # TODO use wait_for here too
        if check:
            if status.returncode != 0:
                raise Exception(f"Error running command {command};\nstdout: {stdout}\nstderr: {stderr}")
        text = stdout.decode('utf-8')
        self.log.debug('cmd output: `{text}`'.format(text=text))
        return text


class System(Information):
    """
    Used to describe some system, typically localhost
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dict = None
    
    def clear_search(self):
        self.dict = None

    def _apt_list_helper(self, text):
        """
        parsing logic for apt_list
        This lets us use both the async ans sync versions
        """
        # Looks like
        # `python/bionic,now 2.7.15~rc1-1 amd64 [installed]`
        # `apt/bionic,now 1.6.1 amd64 [installed]`
        # `acr/bionic 1.2-1 all`
        # `adacontrol/bionic 1.19r10-2 amd64`
        # `g++/bionic,now 4:7.3.0-3ubuntu2 amd64 [installed,automatic]`
        # `libcudnn7/unknown 7.2.1.38-1+cuda9.2 amd64 [upgradable from: 7.2.1.38-1+cuda9.0]`
        # I don't think there can be spaced in the version
        for line in text.split('\n'):
            if 'Listing...' in line:
                # We skip this line
                continue
            try:
                vars = line.split()
                if not vars:
                    continue
                container = {}

                name = vars[0].split('/')[0]
                container['from'] = 'apt'
                container['name'] = name
                container['version'] = vars[1]

                if len(vars[2:]) == 1:
                    container['arch'] = vars[2]
                else:
                    container['arch'] = vars[2]
                    # The state may be multiple words, but it will be the rest
                    container['state'] = ' '.join(vars[3:])

                    # If we have an installed version, and there is an upgrade available, it will be in the state
                    if 'upgradable' in container['state']:
                        _version = re.match(r'\[upgradable from: (.*)\]', container['state']).groups()[0]
                        container['version'] = _version

                self.log.debug("Apt app: {container}".format(container=container))
                yield container
            except Exception as e:
                self.log.warning("Problem with line: {line}; {e}".format(line=line, e=e))

    def apt_list(self, apps=None):
        """
        Return a generator with each item being a line in the output of `apt list`
        apt list shows the cache of packages it knows about
        Each item is a dictionary with a `name`, `version`, `arch`, and `state` if available
        """
        text = self.get_command_text('apt list {apps}'.format(apps='' if not apps else ' '.join((str(app) for app in apps))), shell=True)

        return self._apt_list_helper(text)

    async def async_apt_list(self, apps=None):
        text = await self.async_get_command_text('apt list {apps}'.format(apps='' if not apps else ' '.join((str(app) for app in apps))))

        return self._apt_list_helper(text)

    def _check_apt_installed(self, app):
        return True if ('state' in app and any([check in app['state'] for check in ['installed', 'upgradable']])) else False

    def apt_installed(self, apps=''):
        """
        Returns a filtered generator of apt applications if the state has 'installed' in it
        """
        return (app for app in self.apt_list(apps) if self._check_apt_installed(app))
    
    async def async_apt_installed(self, apps=''):
        """
        Returns a filtered generator of apt applications if the state has 'installed' in it
        """
        return (app for app in await self.async_apt_list(apps) if self._check_apt_installed(app))
    
    def _apt_manually_installed_helper(self, text):
        # Extract out the commands issued
        apt_commands = re.findall(r'Commandline: (.*)', text)

        # Filter out things we don't want
        def filter_func(word):
            if word.startswith('-'):
                return False
            if word in ('apt-get', 'apt', 'upgrade', 'install'):
                # TODO what if we were upgrading apt?
                return False
            if not long and 'cuda' in word:
                return False
            return True

        apt_packages = (word for command in apt_commands for word in command.split() if filter_func(word))
        self.log.debug("Manual apt packages: `{apt_packages}`".format(apt_packages=apt_packages))
        
        # Remove any pinned parts of the packages; we get the information independent of the pin
        apt_packages = (word[:word.find('=')] if '=' in word else word for word in apt_packages)
        # Loop up the package info
        return apt_packages

    def apt_manually_installed(self, long=True):
        """
        Get a generator of packages that were manually installed via apt along with their versions

        long will add cuda packages from the list
        """
        text = self.get_command_text("cat /var/log/apt/history.log", shell=True)
        
        return self.apt_installed(self._apt_manually_installed_helper(text))
    
    async def async_apt_manually_installed(self, long=True):
        """
        Get a generator of packages that were manually installed via apt along with their versions

        long will add cuda packages from the list
        """
        text = await self.async_get_command_text("cat /var/log/apt/history.log", shell=True)
        
        return self.async_apt_installed(self._apt_manually_installed_helper(text))
    
    def pip_list(self, long=True):
        if long:
            cmd = 'pip list --format json'
        else:
            cmd = 'pip list --format json --not-required'
        lst = json.loads(self.get_command_text(cmd, shell=True))
        for app in lst:
            app['from'] = 'pip'
        return lst
    
    async def async_pip_list(self, long=True):
        if long:
            cmd = 'pip list --format json'
        else:
            cmd = 'pip list --format json --not-required'
        lst = json.loads(await self.async_get_command_text(cmd))
        for app in lst:
            app['from'] = 'pip'
        return lst
    
    def get_multiple(self, iters):
        return (app for iter in iters for app in iter)
    
    def get_all_installed(self, long=True):
        m = []
        for func, kwargs in ((self.apt_installed, {}), (self.pip_list, {'long':long})):
            try:
                m.append(func(**kwargs))
            except Exception as e:
                self.log.warning("Error getting from `{func}`: `{e}`".format(func=func, e=e))
                continue
        return self.get_multiple(m)
    
    async def async_get_all_installed(self, long=True):
        m = []
        for coroutine in (self.async_apt_installed(), self.async_pip_list(long=long)):
            try:
                m.append(await coroutine)
            except Exception as e:
                self.log.warning("Error getting from `{coroutine}`: `{e}`".format(coroutine=coroutine, e=e))
                continue
        return self.get_multiple(m)
    
    def get_dict(self, long=True):
        d = {}
        for app in self.get_all_installed(long=long):
            name = app['name']
            if name in d:
                # TODO what do we want to do here?
                self.log.warning("Multiple packages found with the same name. Using first: `{dapp}`;`{app}`".format(dapp=d[app['name']], app=app))
                continue
            d[name] = app
        self.dict = d
        return d
    
    async def async_get_dict(self, long=True):
        d = {}
        for app in await self.async_get_all_installed(long=long):
            name = app['name']
            if name in d:
                # TODO what do we want to do here?
                self.log.warning("Multiple packages found with the same name. Using first: `{dapp}`;`{app}`;".format(dapp=d[app['name']], app=app))
                continue
            d[name] = app
        self.dict = d  # We set it so we can use it later
        return d
    
    def _search_helper(self, search_term, dict, version='', match=False):
        filter = lambda name: (search_term == name) if match else (search_term in name)
        lst = [app for name, app in dict.items() if filter(name) and version in app['version']]
        lst.sort(key=lambda app: len(app['name']))  # TODO Shortest match is probably what we want, right?
        return lst

    def search(self, search_term, dict=False, version='', match=False):
        """
        Search a dictionary of app names to their information
        
        search_term: what package to look for
        version: What version to look for
        """
        if not dict:
            if not self.dict:
                self.dict = self.get_dict()
            dict = self.dict
        lst = self._search_helper(search_term, dict=dict, version=version, match=match)
        return lst
    
    async def async_search(self, search_term, dict=False, version='', match=False):
        """
        Search a dictionary of app names to their information
        
        search_term: what package to look for
        version: What version to look for
        """
        if not dict:
            if not self.dict:
                self.dict = await self.async_get_dict()
            dict = self.dict
        lst = self._search_helper(search_term, dict=dict, version=version, match=match)
        return lst


class Singularity(System):
    """
    Get information from within a singularity container
    """
    def __init__(self, image, singularity='singularity', *args, **kwargs):
        """
        image: string of the absolute location of the image
        singularity: string of what binary should be used
        """
        super().__init__(*args, **kwargs)
        self.image = image
        self.pre_command = '{singularity} exec {image} '.format(singularity=singularity, image=image)
        self.stderr_into_stdout = False
