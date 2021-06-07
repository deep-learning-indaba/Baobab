import io
import zipfile


def zip_in_memory(files):

    # Zip all files together
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for file_name, data in files:
            zip_file.writestr(file_name, data.getvalue())

    return zip_buffer