import os
import tempfile
import asyncio


async def merge_audio_files(audio_files: list[str], output_path: str) -> str:
    if not audio_files:
        raise ValueError("No audio files to merge")

    if len(audio_files) == 1:
        os.rename(audio_files[0], output_path)
        return output_path

    file_list_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            file_list_path = f.name
            for af in audio_files:
                normalized = os.path.abspath(af).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{normalized}'\n")

        proc = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            file_list_path,
            "-c",
            "copy",
            "-y",
            output_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(f"ffmpeg merge failed with code {proc.returncode}")

        return output_path
    finally:
        if file_list_path and os.path.exists(file_list_path):
            os.unlink(file_list_path)
        for f in audio_files:
            try:
                os.unlink(f)
            except OSError:
                pass
