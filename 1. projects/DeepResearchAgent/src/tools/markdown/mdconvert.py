import os
from dotenv import load_dotenv
load_dotenv(verbose=True)

from markitdown import MarkItDown
import requests
import io
from typing import BinaryIO, Any
import camelot
import tempfile
from markitdown.converters import PdfConverter
from markitdown.converters import AudioConverter
from markitdown.converters._pdf_converter import _dependency_exc_info
from markitdown.converters._exiftool import exiftool_metadata
from markitdown._stream_info import StreamInfo
from markitdown._base_converter import DocumentConverterResult
from markitdown._exceptions import MissingDependencyException, MISSING_DEPENDENCY_MESSAGE
import pdfminer
import pdfminer.high_level
from litellm import transcription

from src.models import model_manager
from src.logger import logger


def read_tables_from_stream(file_stream):
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as temp_pdf:
        temp_pdf.write(file_stream.read())
        temp_pdf.flush()
        tables = camelot.read_pdf(temp_pdf.name, flavor="lattice")
        return tables

def transcribe_audio(file_stream, audio_format):

    if "whisper" in model_manager.registed_models:
        # Use the Whisper model for transcription
        model = model_manager.registed_models["whisper"]
        result = model(
            file_stream=file_stream,
        )
    else:
        response = transcription(model="gpt-4o-transcribe", file=file_stream).json()
        result = response.get("text", "No transcription available.")

    return result

class AudioWhisperConverter(AudioConverter):

    def convert(
            self,
            file_stream: BinaryIO,
            stream_info: StreamInfo,
            **kwargs: Any,  # Options to pass to the converter
    ) -> DocumentConverterResult:
        md_content = ""

        # Add metadata
        metadata = exiftool_metadata(
            file_stream, exiftool_path=kwargs.get("exiftool_path")
        )
        if metadata:
            for f in [
                "Title",
                "Artist",
                "Author",
                "Band",
                "Album",
                "Genre",
                "Track",
                "DateTimeOriginal",
                "CreateDate",
                # "Duration", -- Wrong values when read from memory
                "NumChannels",
                "SampleRate",
                "AvgBytesPerSec",
                "BitsPerSample",
            ]:
                if f in metadata:
                    md_content += f"{f}: {metadata[f]}\n"

        # Figure out the audio format for transcription
        if stream_info.extension == ".wav" or stream_info.mimetype == "audio/x-wav":
            audio_format = "wav"
        elif stream_info.extension == ".mp3" or stream_info.mimetype == "audio/mpeg":
            audio_format = "mp3"
        elif (
                stream_info.extension in [".mp4", ".m4a"]
                or stream_info.mimetype == "video/mp4"
        ):
            audio_format = "mp4"
        else:
            audio_format = None

        # Transcribe
        if audio_format:
            try:
                transcript = transcribe_audio(file_stream, audio_format=audio_format)
                if transcript:
                    md_content += "\n\n### Audio Transcript:\n" + transcript
            except MissingDependencyException:
                pass

        # Return the result
        return DocumentConverterResult(markdown=md_content.strip())

class PdfWithTableConverter(PdfConverter):
    def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,  # Options to pass to the converter
    ) -> DocumentConverterResult:
        # Check the dependencies
        if _dependency_exc_info is not None:
            raise MissingDependencyException(
                MISSING_DEPENDENCY_MESSAGE.format(
                    converter=type(self).__name__,
                    extension=".pdf",
                    feature="pdf",
                )
            ) from _dependency_exc_info[
                1
            ].with_traceback(  # type: ignore[union-attr]
                _dependency_exc_info[2]
            )

        assert isinstance(file_stream, io.IOBase)  # for mypy

        tables = read_tables_from_stream(file_stream)
        num_tables = tables.n
        if num_tables == 0:
            return DocumentConverterResult(
                markdown=pdfminer.high_level.extract_text(file_stream),
            )
        else:
            markdown_content = pdfminer.high_level.extract_text(file_stream)
            table_content = ""
            for i in range(num_tables):
                table = tables[i].df
                table_content += f"Table {i + 1}:\n" + table.to_markdown(index=False) + "\n\n"
            markdown_content += "\n\n" + table_content
            return DocumentConverterResult(
                markdown=markdown_content,
            )

class MarkitdownConverter():
    def __init__(self,
                 use_llm: bool = False,
                 model_id: str = None,
                 timeout: int = 30):

        self.timeout = timeout
        self.use_llm = use_llm
        self.model_id = model_id

        if use_llm:
            client = model_manager.registed_models(model_id).http_client
            self.client = MarkItDown(
                enable_plugins=True,
                llm_client=client,
                llm_model=model_id,
            )
        else:
            self.client = MarkItDown(
                enable_plugins=True,
            )

        removed_converters = [
            PdfConverter, AudioConverter
        ]

        self.client._converters = [
            converter for converter in self.client._converters
            if not isinstance(converter.converter, tuple(removed_converters))
        ]
        self.client.register_converter(PdfWithTableConverter())
        self.client.register_converter(AudioWhisperConverter())

    def convert(self, source: str, **kwargs: Any):
        try:
            result = self.client.convert(
                source,
                **kwargs)
            return result
        except Exception as e:
            logger.error(f"Error during conversion: {e}")
            return None