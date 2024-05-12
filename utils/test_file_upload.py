# import requests

# # URL of the endpoint to send the file to
# url = "http://127.0.0.1:8000/organization/1/uploadfile?weaviate_class=Maternal_health"

# # Path to the file to be sent
# file_path = "data/Womens-Health-Book.pdf"

# # Open the file in binary mode and prepare it for sending
# with open(file_path, "rb") as file:
#     files = {"file": (file_path, file, "application/octet-stream")}

#     # Send the file to the endpoint using a POST request
#     response = requests.post(url, files=files)

# # Check the response
# if response.status_code == 200:
#     print("File uploaded successfully!")
#     print(response.json())
# else:
#     print("Failed to upload the file.")
#     print(response.content)
