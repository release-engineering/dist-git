""" test clone url parser """

from dist_git_client import parse_clone_url


def _checker(url, hostname, path):
    parsed = parse_clone_url(url)
    assert parsed.hostname == hostname
    assert parsed.path == path


def test_parse_clone_urls():
    """ Basic clone url formats """
    _checker("git@github.com:example/example-project.git",
             "github.com", "example/example-project.git")
    _checker("https://github.com/example/example-project.git",
             "github.com", "/example/example-project.git")
    _checker("https://github.com/example/example-project",
             "github.com", "/example/example-project")
    _checker("ssh://jdoe@pkgs.fedoraproject.org/rpms/example.git",
             "pkgs.fedoraproject.org", "/rpms/example.git")
    _checker("https://copr-dist-git.fedorainfracloud.org/git"
             "/@abrt/retrace-server-devel/retrace-server.git",
             "copr-dist-git.fedorainfracloud.org",
             "/git/@abrt/retrace-server-devel/retrace-server.git")
    _checker("file:///home/foo.git",
             "localhost", "/home/foo.git")
    _checker("/home/foo.git",
             "localhost", "/home/foo.git")
