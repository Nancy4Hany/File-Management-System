
from io import BytesIO

def test_upload_document(client, auth):
    auth.login()
    response = client.post('/upload', data={
        'title': 'Test Document',
        'description': 'A test document',
        'file': (BytesIO(b'my file contents'), 'test.pdf')
    }, content_type='multipart/form-data')
    assert response.status_code == 302  
