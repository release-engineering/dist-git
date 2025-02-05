"""
dist-git-client code, moved to a python module to simplify unit-testing
"""

import argparse
import configparser
import errno
import glob
import logging
import shlex
import os
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urlparse

try:
    from rpmautospec import (
        specfile_uses_rpmautospec as rpmautospec_used,
        process_distgit as rpmautospec_expand,
    )
except ImportError:
    rpmautospec_used = lambda _: False


def log_cmd(command, comment="Running command"):
    """ Dump the command to stderr so it can be c&p to shell """
    command = ' '.join([shlex.quote(x) for x in command])
    logging.info("%s: %s", comment, command)


def check_output(cmd, comment="Reading stdout from command"):
    """ el6 compatible subprocess.check_output() """
    log_cmd(cmd, comment)
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, _) = process.communicate()
    if process.returncode:
        raise RuntimeError("Exit non-zero: {0}".format(process.returncode))
    return stdout

def call(cmd, comment="Calling"):
    """ wrap sp.call() with logging info """
    log_cmd(cmd, comment)
    return subprocess.call(cmd)

def check_call(cmd, comment="Checked call"):
    """ wrap sp.check_call() with logging info """
    log_cmd(cmd, comment)
    subprocess.check_call(cmd)

def _load_config(directory):
    config = configparser.ConfigParser()
    files = glob.glob(os.path.join(directory, "*.ini"))
    logging.debug("Files %s in config directory %s", files, directory)
    config.read(files)

    config_dict = {
        "instances": {},
        "clone_host_map": {},
    }

    instances = config_dict["instances"]
    for section_name in config.sections():
        section = config[section_name]
        instance = instances[section_name] = {}
        for key in section.keys():
            # array-like config options
            if key in ["clone_hostnames", "path_prefixes"]:
                hostnames = section[key].split()
                instance[key] = [h.strip() for h in hostnames]
            else:
                instance[key] = section[key]

        for key in ["sources", "specs"]:
            if key in instance:
                continue
            instance[key] = "."

        if "sources_file" not in instance:
            instance["sources_file"] = "sources"

        if "default_sum" not in instance:
            instance["default_sum"] = "md5"

        for host in instance["clone_hostnames"]:
            if host not in config_dict["clone_host_map"]:
                config_dict["clone_host_map"][host] = {}
            host_dict = config_dict["clone_host_map"][host]
            for prefix in instance.get("path_prefixes", ["DEFAULT"]):
                if prefix in host_dict:
                    msg = "Duplicate prefix {0} for {1} hostname".format(
                        prefix, host,
                    )
                    raise RuntimeError(msg)
                host_dict[prefix] = instance

    return config_dict


def download(url, filename):
    """ Download URL as FILENAME using curl command """

    if not hasattr(download, "curl_has_retry_all_errors"):
        # Drop this once EL8 is not a thing to support
        output = check_output(["curl", "--help", "all"])
        # method's static variable to avoid using 'global'
        download.curl_has_retry_all_errors = b"--retry-all-errors" in output

    command = [
        "curl",
        "-H", "Pragma:",
        "-o", filename,
        "--location",
        "--connect-timeout", "60",
        "--retry", "3", "--retry-delay", "10",
        "--remote-time",
        "--show-error",
        "--fail",
    ]

    if download.curl_has_retry_all_errors:
        command += ["--retry-all-errors"]

    if call(command + [url]):
        raise RuntimeError("Can't download file {0}".format(filename))


def mkdir_p(path):
    """ mimic 'mkdir -p <path>' command """
    try:
        os.makedirs(path)
    except OSError as err:
        if err.errno != errno.EEXIST:
            raise


def download_file_and_check(url, params, distgit_config):
    """ Download given URL (if not yet downloaded), and try the checksum """
    filename = params["filename"]
    sum_binary = params["hashtype"] + "sum"

    mkdir_p(distgit_config["sources"])

    if not os.path.exists(filename):
        logging.info("Downloading %s", filename)
        download(url, filename)
    else:
        logging.info("File %s already exists", filename)

    sum_command = [sum_binary, filename]
    output = check_output(sum_command).decode("utf-8")
    checksum, _ = output.strip().split()
    if checksum != params["hash"]:
        raise RuntimeError("Check-sum {0} is wrong, expected: {1}".format(
            checksum,
            params["hash"],
        ))


def _detect_clone_url():
    git_config = ".git/config"
    if not os.path.exists(git_config):
        msg = "{0} not found, $PWD is not a git repository".format(git_config)
        raise RuntimeError(msg)

    git_conf_reader = configparser.ConfigParser()
    git_conf_reader.read(git_config)
    return git_conf_reader['remote "origin"']["url"]


def get_distgit_config(config, forked_from=None):
    """
    Given the '.git/config' file from current directory, return the
    appropriate part of dist-git configuration.
    Returns tuple: (urlparse(clone_url), distgit_config)
    """
    url = forked_from
    if not url:
        url = _detect_clone_url()
    parsed_url = urlparse(url)
    if parsed_url.hostname is None:
        hostname = "localhost"
    else:
        hostname = parsed_url.hostname

    prefixes = config["clone_host_map"][hostname]
    prefix_found = None
    for prefix in prefixes.keys():
        if not parsed_url.path.startswith(prefix):
            continue
        prefix_found = prefix

    if not prefix_found:
        if "DEFAULT" not in prefixes:
            raise RuntimeError("Path {0} does not match any of 'path_prefixes' "
                               "for '{1}' hostname".format(parsed_url.path,
                                                           hostname))
        prefix_found = "DEFAULT"

    return parsed_url, prefixes[prefix_found]


def get_spec(distgit_config):
    """
    Find the specfile name inside distgit_config["specs"] directory
    """
    spec_dir = distgit_config["specs"]
    specfiles = glob.glob(os.path.join(spec_dir, '*.spec'))
    if len(specfiles) != 1:
        abs_spec_dir = os.path.join(os.getcwd(), spec_dir)
        message = "Exactly one spec file expected in {0} directory, {1} found".format(
            abs_spec_dir, len(specfiles),
        )
        raise RuntimeError(message)
    specfile = os.path.basename(specfiles[0])
    return specfile


def parse_sources(args, config):
    """
    Locate the sources, and download them from the appropriate dist-git
    lookaside cache.
    """
    # pylint: disable=too-many-locals
    parsed_url, distgit_config = get_distgit_config(config, args.forked_from)
    namespace = parsed_url.path.strip('/').split('/')
    # drop the last {name}.git part
    repo_name = namespace.pop()
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]
    namespace = list(reversed(namespace))

    output = check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    output = output.decode("utf-8").strip()
    if output == "HEAD":
        output = check_output(["git", "rev-parse", "HEAD"])
        output = output.decode("utf-8").strip()
    refspec = output
    specfile = get_spec(distgit_config)
    name = specfile[:-5]
    sources_file = distgit_config["sources_file"].format(name=name)
    if not os.path.exists(sources_file):
        logging.info("'%s' file not found, download skipped", sources_file)
        return

    logging.info("Reading sources specification file: %s", sources_file)
    with open(sources_file, 'r', encoding="utf8") as sfd:
        while True:
            line = sfd.readline()
            if not line:
                break

            kwargs = {
                "name": repo_name,
                "refspec": refspec,
                "namespace": namespace,
            }

            source_spec = line.split()
            if not source_spec:
                # line full of white-spaces, skip
                continue

            if len(source_spec) == 2:
                # old md5/sha1 format: 0ced6f20b9fa1bea588005b5ad4b52c1  tar-1.26.tar.xz
                kwargs["hashtype"] = distgit_config["default_sum"].lower()
                kwargs["hash"] = source_spec[0]
                kwargs["filename"] = source_spec[1]
            elif len(source_spec) == 4:
                # SHA512 (tar-1.30.tar.xz.sig) = <HASH>
                kwargs["hashtype"] = source_spec[0].lower()
                kwargs["hash"] = source_spec[3]
                filename = os.path.basename(source_spec[1])
                kwargs["filename"] = filename.strip('()')
            else:
                msg = f"Weird sources line: {line}"
                raise RuntimeError(msg)

            url_file = '/'.join([
                distgit_config["lookaside_location"],
                distgit_config["lookaside_uri_pattern"].format(**kwargs)
            ])

            yield url_file, kwargs, distgit_config


def sources(args, config):
    """
    Go through all the dist-git files, and download them.
    """
    for url, metadata, distgit_config in parse_sources(args, config):
        download_file_and_check(url, metadata, distgit_config)


def handle_autospec(spec_abspath, spec_basename, args):
    """
    When %auto* macros are used in SPEC_ABSPATH, expand them into a separate
    spec file within ARGS.OUTPUTDIR, and return the absolute filename of the
    specfile.  When %auto* macros are not used, return SPEC_ABSPATH unchanged.
    """
    result = spec_abspath
    if rpmautospec_used(spec_abspath):
        git_dir = check_output(["git", "rev-parse", "--git-dir"])
        git_dir = git_dir.decode("utf-8").strip()
        if os.path.exists(os.path.join(git_dir, "shallow")):
            # Hack.  The rpmautospec doesn't support shallow clones:
            # https://pagure.io/fedora-infra/rpmautospec/issue/227
            logging.info("rpmautospec requires full clone => --unshallow")
            check_call(["git", "fetch", "--unshallow"])

        # Expand the %auto* macros, and create the separate spec file in the
        # output directory.
        output_spec = os.path.join(args.outputdir, spec_basename)
        rpmautospec_expand(spec_abspath, output_spec)
        result = output_spec
    return result


def _prepare_outputdir(args):
    mkdir_p(args.outputdir)


def _get_preprocessed_specfile(distgit_config, args):
    specs = os.path.join(os.getcwd(), distgit_config["specs"])
    spec = get_spec(distgit_config)
    spec_abspath = os.path.join(specs, spec)
    return handle_autospec(spec_abspath, spec, args)


def srpm(args, config):
    """
    Using the appropriate dist-git configuration, generate source RPM
    file.  This requires running 'def sources()' first.
    """
    _, distgit_config = get_distgit_config(config, args.forked_from)
    _prepare_outputdir(args)
    spec_abspath = _get_preprocessed_specfile(distgit_config, args)
    sources_dir = os.path.join(os.getcwd(), distgit_config["sources"])

    if args.mock_chroot:
        command = [
            "mock", "--buildsrpm",
            "-r", args.mock_chroot,
            "--spec", spec_abspath,
            "--sources", sources_dir,
            "--resultdir", args.outputdir,
        ]
    else:
        command = [
            "rpmbuild", "-bs", spec_abspath,
            "--define", "dist %nil",
            "--define", "_sourcedir {0}".format(sources_dir),
            "--define", "_srcrpmdir {0}".format(args.outputdir),
            "--define", "_disable_source_fetch 1",
        ]

    if args.dry_run or 'COPR_DISTGIT_CLIENT_DRY_RUN' in os.environ:
        log_cmd(command, comment="Dry run")
    else:
        check_call(command)


def _list_git_sources(subdir):
    directory = os.path.normpath(subdir) + "/"
    cmd = ["git", "ls-tree", "HEAD", directory]
    git_output = subprocess.check_output(cmd, encoding="utf-8")
    for line in git_output.splitlines():
        _, objtype, _, name = line.split()
        if objtype == "blob":
            yield name


def snapshot(args, config):
    """
    Generate a tarball snapshot for given checkout.
    """
    _, distgit_instance_config = get_distgit_config(config, args.forked_from)
    spec = _get_preprocessed_specfile(distgit_instance_config, args)

    with tempfile.TemporaryDirectory(prefix="copr-test-walk") as workdir:
        tar_name = os.path.basename(spec)[:-5]
        tar_dir = os.path.join(workdir, tar_name)
        os.makedirs(tar_dir)

        # We insert every file top-level, while git in general may store them in
        # the sources subdir.  Bomb early if double should be added.
        basenames_added = set()
        def _prepare_file(file):
            basename = os.path.basename(file)
            if basename in basenames_added:
                raise RuntimeError(f"{basename} added twice")
            basenames_added.add(basename)
            shutil.copy(file, tar_dir)

        _prepare_file(spec)

        for _, metadata, _ in parse_sources(args, config):
            print("..")
            _prepare_file(metadata["filename"])

        for file in _list_git_sources(distgit_instance_config["sources"]):
            if os.path.basename(file) == os.path.basename(spec):
                # spec file added separately
                continue
            # Shall we filter-out files that are not related to RPM
            # building?
            _prepare_file(file)

        tarball = os.path.join(args.outputdir, tar_name + ".tar.gz")
        logging.info("Generating tarball %s", tarball)
        tar_cmd = ["tar", "--owner=root", "--group=root", "--format=pax",
                   "-czf", tarball, "-C", workdir, tar_name]
        subprocess.check_call(tar_cmd)


def clone(args, config):
    """
    Automatically clone a package from a given DistGit instance
    """
    distgit = config["instances"][args.dist_git]
    parts = distgit.get("cloning_pattern_package_parts")
    if parts:
        expected = parts.split()
        have = args.package.split("/")
        if len(expected) != len(have):
            raise RuntimeError(
                "Package '{0}' has a wrong format, {1} "
                "slash-separated parts are expected: {2}".format(
                    args.package, len(expected),
                    "/".join(expected),
            ))

    clone_url = distgit["cloning_pattern"].format(package=args.package)
    check_call([
        "git", "clone", clone_url,
    ])

def _get_argparser():
    parser = argparse.ArgumentParser(prog="dist-git-client",
                                     description="""\
A simple, configurable python utility that is able to download sources from
various dist-git instances, and generate source RPMs.
The utility is able to automatically map the "origin" .git/config clone URL
(or --forked-from URL, if specified) to a corresponding dist-git instance
configured in /etc/dist-git-client directory.
""")

    # main parser
    default_confdir = os.environ.get("COPR_DISTGIT_CLIENT_CONFDIR",
                                     "/etc/dist-git-client")
    parser.add_argument(
        "--configdir", default=default_confdir,
        help="Where to load configuration files from")
    parser.add_argument(
        "--loglevel", default="info",
        help="Python logging level, e.g. debug, info, error")
    parser.add_argument(
        "--forked-from",
        metavar="CLONE_URL",
        help=("Specify that this git clone directory is a dist-git repository "
              "fork.  If used, the default clone url detection from the "
              ".git/config file is disabled and CLONE_URL is used instead. "
              "This specified CLONE_URL is used to detect the appropriate "
              "lookaside cache pattern to download the sources."))

    subparsers = parser.add_subparsers(
        title="actions", dest="action")

    # sources parser
    subparsers.add_parser(
        "sources",
        description=(
            "Using the 'url' .git/config, detect where the right DistGit "
            "lookaside cache exists, and download the corresponding source "
            "files."),
        help="Download sources from the lookaside cache")

    # srpm parser
    srpm_parser = subparsers.add_parser(
        "srpm",
        help="Generate a source RPM",
        description=(
            "Generate a source RPM from the downloaded source files "
            "by 'sources' command, please run 'sources' first."),
    )
    srpm_parser.add_argument(
        "--outputdir",
        default="/tmp",
        help="Where to store the resulting source RPM")
    srpm_parser.add_argument(
        "--mock-chroot",
        help=("Generate the SRPM in mock buildroot instead of on host.  The "
              "argument is passed down to mock as the 'mock -r|--root' "
              "argument."),
    )
    srpm_parser.add_argument(
        "--dry-run", action="store_true",
        help=("Don't produce the SRPM, just print the command which would be "
              "otherwise called"),
    )

    clone_parser = subparsers.add_parser(
        "clone",
        help="Clone package from a DistGit source",
    )

    clone_parser.add_argument(
        "--dist-git",
        default="fedora",
        help=("The DistGit ID as configured in /etc/dist-git-client/"),
    )

    clone_parser.add_argument(
        "package",
        default="fedora",
        help=("Package name specification.  For some DistGit "
              "instances this consists of multiple parts separated "
              "by slash, e.g. for '--dist-git=fedora-copr' use "
              "'@copr/copr-dev/copr-cli'."),
    )

    snapshot_parser = subparsers.add_parser(
        "snapshot",
        help=("Generate a snapshot for given dist-git checkout"),
    )
    snapshot_parser.add_argument(
        "--outputdir",
        default="/tmp",
        help="Where to store the resulting tarball")

    return parser


def unittests_init_git(files=None):
    """
    Initialize .git/ directory.  This method is only used for unit-testing.
    """
    check_output(["git", "init", ".", "-b", "main"])
    shutil.rmtree(".git/hooks")
    check_output(["git", "config", "user.email", "you@example.com"])
    check_output(["git", "config", "user.name", "Your Name"])
    check_output(["git", "config", "advice.detachedHead", "false"])

    for filename, content in files:
        dirname = os.path.dirname(filename)
        try:
            os.makedirs(dirname)
        except OSError:
            pass
        with open(filename, "w", encoding="utf-8") as filed:
            filed.write(content)
        check_output(["git", "add", filename])

    check_output(["git", "commit", "-m", "initial"])


def main():
    """ The entrypoint for the whole logic """
    args = _get_argparser().parse_args()
    logging.basicConfig(
        level=getattr(logging, args.loglevel.upper()),
        format="%(levelname)s: %(message)s",
    )
    config = _load_config(args.configdir)

    try:
        if args.action == "srpm":
            srpm(args, config)
        elif args.action == "clone":
            clone(args, config)
        elif args.action == "snapshot":
            snapshot(args, config)
        else:
            sources(args, config)
    except RuntimeError as err:
        logging.error("%s", err)
        sys.exit(1)
