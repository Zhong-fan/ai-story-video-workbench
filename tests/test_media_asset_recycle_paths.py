from __future__ import annotations

import unittest
from pathlib import Path

from app.media_asset_recycle import media_asset_file_path
from app.models import MediaAsset


class MediaAssetPathTests(unittest.TestCase):
    def test_media_asset_file_path_uses_project_and_asset_codes(self) -> None:
        asset = MediaAsset(id=123, project_id=1, asset_type="shot_first_frame")
        settings = type("SettingsStub", (), {"output_dir": Path("output")})()

        path = media_asset_file_path(asset, settings=settings, file_name="first-frame.png")

        self.assertEqual(path.as_posix(), "output/projects/p000001/assets/media/m000123/first-frame.png")

    def test_deleted_media_asset_file_path_stays_under_project_deleted_directory(self) -> None:
        asset = MediaAsset(id=123, project_id=1, asset_type="shot_first_frame")
        settings = type("SettingsStub", (), {"output_dir": Path("output")})()

        path = media_asset_file_path(asset, settings=settings, file_name="first-frame.png", deleted=True)

        self.assertEqual(path.as_posix(), "output/projects/p000001/deleted/media/m000123/first-frame.png")


if __name__ == "__main__":
    unittest.main()
