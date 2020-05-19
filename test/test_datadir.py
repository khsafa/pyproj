import os

import pytest
from mock import patch

from pyproj import CRS
from pyproj._datadir import pyproj_global_context_initialize
from pyproj.datadir import (
    DataDirError,
    append_data_dir,
    get_data_dir,
    get_user_data_dir,
    set_data_dir,
)
from test.conftest import proj_env


def create_projdb(tmpdir):
    with open(os.path.join(tmpdir, "proj.db"), "w") as pjdb:
        pjdb.write("DUMMY proj.db")


_INVALID_PATH = "/invalid/path/to/nowhere"


def setup_os_mock(os_mock, abspath_return=_INVALID_PATH, proj_dir=None):
    os_mock.path.abspath.return_value = abspath_return
    os_mock.path.join = os.path.join
    os_mock.path.dirname = os.path.dirname
    os_mock.path.exists = os.path.exists
    os_mock.pathsep = os.pathsep
    if proj_dir is None:
        os_mock.environ = {}
    else:
        os_mock.environ = {"PROJ_LIB": proj_dir}


def test_get_data_dir__missing():
    with proj_env(), pytest.raises(DataDirError), patch(
        "pyproj.datadir.find_executable", return_value=None
    ), patch("pyproj.datadir.os") as os_mock, patch("pyproj.datadir.sys") as sys_mock:
        sys_mock.prefix = _INVALID_PATH
        setup_os_mock(os_mock)
        assert get_data_dir() is None


def test_pyproj_global_context_initialize__datadir_missing():
    with proj_env(), pytest.raises(DataDirError), patch(
        "pyproj._datadir.get_data_dir", side_effect=DataDirError("test")
    ):
        pyproj_global_context_initialize()


def test_get_data_dir__from_user(tmp_path):
    tmpdir = tmp_path / "proj"
    tmpdir.mkdir()
    tmpdir = str(tmpdir)
    tmpdir_env = tmp_path / "proj_env"
    tmpdir_env.mkdir()
    tmpdir_env = str(tmpdir_env)
    with proj_env(), patch("pyproj.datadir.os") as os_mock, patch(
        "pyproj.datadir.sys"
    ) as sys_mock:  # noqa: E501
        setup_os_mock(
            os_mock,
            abspath_return=os.path.join(tmpdir, "randomfilename.py"),
            proj_dir=tmpdir_env,
        )
        sys_mock.prefix = tmpdir_env
        create_projdb(tmpdir)
        create_projdb(tmpdir_env)
        set_data_dir(tmpdir)
        internal_proj_dir = os.path.join(tmpdir, "proj_dir", "share", "proj")
        os.makedirs(internal_proj_dir)
        create_projdb(internal_proj_dir)
        assert get_data_dir() == tmpdir


def test_get_data_dir__internal(tmp_path):
    tmpdir = tmp_path / "proj"
    tmpdir.mkdir()
    tmpdir = str(tmpdir)
    tmpdir_fake = tmp_path / "proj_fake"
    tmpdir_fake.mkdir()
    tmpdir_fake = str(tmpdir_fake)
    with proj_env(), patch("pyproj.datadir.os") as os_mock, patch(
        "pyproj.datadir.sys"
    ) as sys_mock:
        setup_os_mock(
            os_mock,
            abspath_return=os.path.join(tmpdir, "randomfilename.py"),
            proj_dir=tmpdir_fake,
        )
        sys_mock.prefix = tmpdir_fake
        create_projdb(tmpdir)
        create_projdb(tmpdir_fake)
        internal_proj_dir = os.path.join(tmpdir, "proj_dir", "share", "proj")
        os.makedirs(internal_proj_dir)
        create_projdb(internal_proj_dir)
        assert get_data_dir() == internal_proj_dir


def test_get_data_dir__from_env_var(tmp_path):
    tmpdir = str(tmp_path)
    with proj_env(), patch("pyproj.datadir.os") as os_mock, patch(
        "pyproj.datadir.sys"
    ) as sys_mock:
        setup_os_mock(os_mock, proj_dir=tmpdir)
        sys_mock.prefix = _INVALID_PATH
        create_projdb(tmpdir)
        assert get_data_dir() == tmpdir


def test_get_data_dir__from_env_var__multiple(tmp_path):
    tmpdir = str(tmp_path)
    with proj_env(), patch("pyproj.datadir.os") as os_mock, patch(
        "pyproj.datadir.sys"
    ) as sys_mock:
        setup_os_mock(os_mock, proj_dir=os.pathsep.join([tmpdir, tmpdir, tmpdir]))
        sys_mock.prefix = _INVALID_PATH
        create_projdb(tmpdir)
        assert get_data_dir() == os.pathsep.join([tmpdir, tmpdir, tmpdir])


def test_get_data_dir__from_prefix(tmp_path):
    tmpdir = str(tmp_path)
    with proj_env(), patch("pyproj.datadir.os") as os_mock, patch(
        "pyproj.datadir.sys"
    ) as sys_mock:
        setup_os_mock(os_mock)
        sys_mock.prefix = tmpdir
        proj_dir = os.path.join(tmpdir, "share", "proj")
        os.makedirs(proj_dir)
        create_projdb(proj_dir)
        assert get_data_dir() == proj_dir


def test_get_data_dir__from_path(tmp_path):
    tmpdir = str(tmp_path)
    with proj_env(), patch("pyproj.datadir.os") as os_mock, patch(
        "pyproj.datadir.sys"
    ) as sys_mock, patch("pyproj.datadir.find_executable") as find_exe:
        setup_os_mock(os_mock)
        sys_mock.prefix = _INVALID_PATH
        find_exe.return_value = os.path.join(tmpdir, "bin", "proj")
        proj_dir = os.path.join(tmpdir, "share", "proj")
        os.makedirs(proj_dir)
        create_projdb(proj_dir)
        assert get_data_dir() == proj_dir


def test_append_data_dir__internal(tmp_path):
    tmpdir = str(tmp_path)
    with proj_env(), patch("pyproj.datadir.os") as os_mock:
        setup_os_mock(os_mock, os.path.join(tmpdir, "randomfilename.py"))
        create_projdb(tmpdir)
        internal_proj_dir = os.path.join(tmpdir, "proj_dir", "share", "proj")
        os.makedirs(internal_proj_dir)
        create_projdb(internal_proj_dir)
        extra_datadir = str(os.path.join(tmpdir, "extra_datumgrids"))
        append_data_dir(extra_datadir)
        assert get_data_dir() == os.pathsep.join([internal_proj_dir, extra_datadir])


def test_creating_multiple_crs_without_file_limit():
    assert [CRS.from_epsg(4326) for _ in range(1200)]


def test_get_user_data_dir():
    assert get_user_data_dir().endswith("proj")
