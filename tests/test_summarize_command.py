"""
Tests for lib/commands/summarize.py  (rewritten for Nextflow-based implementation)

The command no longer executes Python summary logic directly — it validates
arguments and delegates to `nextflow run`. These tests cover everything that
can be verified without invoking Nextflow:

  - --list displays registered summary types
  - --type validation (unknown type, missing type)
  - directory argument validation (paths must exist, at least one required)
  - _build_nextflow_command produces correct flags and ordering
  - --dry-run prints the plan without executing
  - --resume inserts -resume correctly
  - backend selection (conda vs singularity profile flag)
  - _execute_nextflow handles FileNotFoundError gracefully
"""

import argparse
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from commands.summarize import SummarizeCommand, _KNOWN_SUMMARIES


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _args(
    type=None,
    list=False,
    outdir="summaries",
    bacterial_outdir=None,
    annotation_outdir=None,
    format="tsv",
    resume=False,
    dry_run=False,
):
    return argparse.Namespace(
        type=type,
        list=list,
        outdir=outdir,
        bacterial_outdir=bacterial_outdir,
        annotation_outdir=annotation_outdir,
        format=format,
        resume=resume,
        dry_run=dry_run,
    )


@pytest.fixture
def cmd():
    return SummarizeCommand()


# ---------------------------------------------------------------------------
# --list
# ---------------------------------------------------------------------------

class TestListMode:

    def test_list_returns_true(self, cmd, capsys):
        assert cmd.run(_args(list=True)) is True

    def test_list_prints_all_known_types(self, cmd, capsys):
        cmd.run(_args(list=True))
        output = capsys.readouterr().out
        for name in _KNOWN_SUMMARIES:
            assert name in output

    def test_list_prints_descriptions(self, cmd, capsys):
        cmd.run(_args(list=True))
        output = capsys.readouterr().out
        for desc in _KNOWN_SUMMARIES.values():
            assert desc in output

    def test_list_needs_no_outdir(self, cmd):
        assert cmd.run(_args(list=True)) is True


# ---------------------------------------------------------------------------
# --type validation
# ---------------------------------------------------------------------------

class TestTypeValidation:

    def test_missing_type_returns_false(self, cmd, capsys):
        assert cmd.run(_args()) is False
        assert "Error" in capsys.readouterr().out

    def test_unknown_type_returns_false(self, cmd, tmp_path, capsys):
        result = cmd.run(_args(
            type="not_a_real_summary",
            bacterial_outdir=str(tmp_path),
        ))
        assert result is False
        assert "Unknown" in capsys.readouterr().out

    def test_unknown_type_suggests_known_types(self, cmd, tmp_path, capsys):
        cmd.run(_args(type="typo", bacterial_outdir=str(tmp_path)))
        output = capsys.readouterr().out
        for name in _KNOWN_SUMMARIES:
            assert name in output


# ---------------------------------------------------------------------------
# Directory validation
# ---------------------------------------------------------------------------

class TestDirectoryValidation:

    def test_no_dirs_at_all_returns_false(self, cmd, capsys):
        result = cmd.run(_args(type="bacterial_genome"))
        assert result is False

    def test_nonexistent_bacterial_outdir_returns_false(self, cmd, tmp_path, capsys):
        result = cmd.run(_args(
            type="bacterial_genome",
            bacterial_outdir=str(tmp_path / "does_not_exist"),
        ))
        assert result is False
        assert "Error" in capsys.readouterr().out

    def test_nonexistent_annotation_outdir_returns_false(self, cmd, tmp_path, capsys):
        result = cmd.run(_args(
            type="prophage_table",
            annotation_outdir=str(tmp_path / "does_not_exist"),
        ))
        assert result is False

    def test_file_path_rejected_as_dir(self, cmd, tmp_path, capsys):
        f = tmp_path / "a_file.txt"
        f.write_text("not a directory")
        result = cmd.run(_args(
            type="bacterial_genome",
            bacterial_outdir=str(f),
        ))
        assert result is False

    def test_bacterial_only_is_valid(self, cmd, bacterial_outdir, tmp_path):
        with patch.object(cmd, "_execute_nextflow", return_value=True) as mock_nf:
            result = cmd.run(_args(
                type="bacterial_genome",
                bacterial_outdir=str(bacterial_outdir),
                outdir=str(tmp_path),
            ))
        assert result is True
        mock_nf.assert_called_once()

    def test_annotation_only_is_valid(self, cmd, annotation_outdir, tmp_path):
        with patch.object(cmd, "_execute_nextflow", return_value=True) as mock_nf:
            result = cmd.run(_args(
                type="prophage_table",
                annotation_outdir=str(annotation_outdir),
                outdir=str(tmp_path),
            ))
        assert result is True
        mock_nf.assert_called_once()


# ---------------------------------------------------------------------------
# _build_nextflow_command
# ---------------------------------------------------------------------------

class TestBuildNextflowCommand:

    def _make_params(self, tmp_path, bacterial=True, annotation=True,
                     backend="singularity", fmt="tsv"):
        return {
            "summary_type":      "bacterial_genome",
            "outdir":            str(tmp_path / "summaries"),
            "bacterial_outdir":  str(tmp_path) if bacterial else "NONE",
            "annotation_outdir": str(tmp_path) if annotation else "NONE",
            "summary_format":    fmt,
            "backend":           backend,
            "cache_location":    None,
        }

    def test_workflow_flag_is_summarize(self, tmp_path):
        cmd = SummarizeCommand()
        params = self._make_params(tmp_path)
        result = cmd._build_nextflow_command(params, _args())
        assert "--workflow" in result
        assert result[result.index("--workflow") + 1] == "summarize"

    def test_summary_type_passed(self, tmp_path):
        cmd = SummarizeCommand()
        params = self._make_params(tmp_path)
        result = cmd._build_nextflow_command(params, _args())
        assert "--summary_type" in result
        assert result[result.index("--summary_type") + 1] == "bacterial_genome"

    def test_conda_profile_added_for_conda_backend(self, tmp_path):
        cmd = SummarizeCommand()
        params = self._make_params(tmp_path, backend="conda")
        result = cmd._build_nextflow_command(params, _args())
        assert "-profile" in result
        assert result[result.index("-profile") + 1] == "conda"

    def test_no_profile_flag_for_singularity(self, tmp_path):
        cmd = SummarizeCommand()
        params = self._make_params(tmp_path, backend="singularity")
        result = cmd._build_nextflow_command(params, _args())
        assert "-profile" not in result

    def test_resume_inserted_after_run(self, tmp_path):
        cmd = SummarizeCommand()
        params = self._make_params(tmp_path)
        result = cmd._build_nextflow_command(params, _args(resume=True))
        assert "-resume" in result
        assert result.index("-resume") < result.index("main.nf") + 1

    def test_format_tsv_passed(self, tmp_path):
        cmd = SummarizeCommand()
        params = self._make_params(tmp_path, fmt="tsv")
        result = cmd._build_nextflow_command(params, _args())
        assert result[result.index("--summary_format") + 1] == "tsv"

    def test_format_csv_passed(self, tmp_path):
        cmd = SummarizeCommand()
        params = self._make_params(tmp_path, fmt="csv")
        result = cmd._build_nextflow_command(params, _args(format="csv"))
        assert result[result.index("--summary_format") + 1] == "csv"

    def test_cache_location_conda(self, tmp_path):
        cmd = SummarizeCommand()
        params = self._make_params(tmp_path, backend="conda")
        params["cache_location"] = "/some/cache"
        result = cmd._build_nextflow_command(params, _args())
        assert "--conda_cache_dir" in result

    def test_cache_location_singularity(self, tmp_path):
        cmd = SummarizeCommand()
        params = self._make_params(tmp_path, backend="singularity")
        params["cache_location"] = "/some/cache"
        result = cmd._build_nextflow_command(params, _args())
        assert "--singularity_cache_dir" in result

    def test_no_cache_flag_when_not_configured(self, tmp_path):
        cmd = SummarizeCommand()
        params = self._make_params(tmp_path)
        result = cmd._build_nextflow_command(params, _args())
        assert "--conda_cache_dir" not in result
        assert "--singularity_cache_dir" not in result


# ---------------------------------------------------------------------------
# --dry-run
# ---------------------------------------------------------------------------

class TestDryRun:

    def test_dry_run_returns_true(self, cmd, bacterial_outdir, tmp_path, capsys):
        result = cmd.run(_args(
            type="bacterial_genome",
            bacterial_outdir=str(bacterial_outdir),
            outdir=str(tmp_path),
            dry_run=True,
        ))
        assert result is True

    def test_dry_run_prints_nextflow_command(self, cmd, bacterial_outdir, tmp_path, capsys):
        cmd.run(_args(
            type="bacterial_genome",
            bacterial_outdir=str(bacterial_outdir),
            outdir=str(tmp_path),
            dry_run=True,
        ))
        assert "nextflow run main.nf" in capsys.readouterr().out

    def test_dry_run_does_not_call_execute(self, cmd, bacterial_outdir, tmp_path):
        with patch.object(cmd, "_execute_nextflow") as mock_nf:
            cmd.run(_args(
                type="bacterial_genome",
                bacterial_outdir=str(bacterial_outdir),
                outdir=str(tmp_path),
                dry_run=True,
            ))
        mock_nf.assert_not_called()

    def test_dry_run_prints_summary_type(self, cmd, bacterial_outdir, tmp_path, capsys):
        cmd.run(_args(
            type="bacterial_genome",
            bacterial_outdir=str(bacterial_outdir),
            outdir=str(tmp_path),
            dry_run=True,
        ))
        assert "bacterial_genome" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# _execute_nextflow error handling
# ---------------------------------------------------------------------------

class TestExecuteNextflow:

    def test_nextflow_not_found_returns_false(self, cmd, capsys):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = cmd._execute_nextflow(["nextflow", "run", "main.nf"])
        assert result is False
        assert "not found" in capsys.readouterr().out.lower()

    def test_nextflow_nonzero_exit_returns_false(self, cmd, capsys):
        mock_result = MagicMock()
        mock_result.returncode = 1
        with patch("subprocess.run", return_value=mock_result):
            result = cmd._execute_nextflow(["nextflow", "run", "main.nf"])
        assert result is False

    def test_nextflow_zero_exit_returns_true(self, cmd, capsys):
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result):
            result = cmd._execute_nextflow(["nextflow", "run", "main.nf"])
        assert result is True
