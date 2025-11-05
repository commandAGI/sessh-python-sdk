"""Integration tests for sessh examples (requires real infrastructure)."""
import os
import pytest
from sessh import SesshClient

# Skip all tests unless SESSH_INTEGRATION_TESTS is set
pytestmark = pytest.mark.skipif(
    not os.environ.get("SESSH_INTEGRATION_TESTS"),
    reason="Set SESSH_INTEGRATION_TESTS=1 to run integration tests"
)


@pytest.fixture
def local_client():
    """Fixture for local client."""
    host = os.environ.get("SESSH_TEST_HOST", "localhost")
    user = os.environ.get("USER", os.environ.get("USERNAME", "user"))
    client = SesshClient(alias="test-local", host=f"{user}@{host}")
    try:
        client.open()
        yield client
    finally:
        client.close()


class TestLocalExample:
    """Test local example integration."""
    
    def test_local_basic_operations(self, local_client):
        """Test basic operations on local host."""
        # Run commands
        local_client.run("echo 'Hello from integration test!'")
        local_client.run("pwd")
        
        # Get logs
        logs = local_client.logs(50)
        assert "integration test" in logs.get("output", "").lower()
        
        # Check status
        status = local_client.status()
        assert status.get("master") == 1
        assert status.get("session") == 1


@pytest.mark.skipif(
    not os.environ.get("AWS_REGION"),
    reason="AWS credentials and region required"
)
class TestAWSExample:
    """Test AWS EC2 example (requires AWS credentials)."""
    
    def test_aws_example_structure(self):
        """Test that AWS example can be imported and has expected structure."""
        from examples import aws
        assert hasattr(aws, "main")


@pytest.mark.skipif(
    not os.environ.get("GCP_PROJECT"),
    reason="GCP project required"
)
class TestGCPExample:
    """Test GCP example (requires GCP credentials)."""
    
    def test_gcp_example_structure(self):
        """Test that GCP example can be imported and has expected structure."""
        from examples import gcp
        assert hasattr(gcp, "main")


@pytest.mark.skipif(
    not os.environ.get("LAMBDA_API_KEY"),
    reason="Lambda Labs API key required"
)
class TestLambdaLabsExample:
    """Test Lambda Labs example (requires API key)."""
    
    def test_lambdalabs_example_structure(self):
        """Test that Lambda Labs example can be imported and has expected structure."""
        from examples import lambdalabs
        assert hasattr(lambdalabs, "main")


@pytest.mark.skipif(
    not os.environ.get("DO_TOKEN"),
    reason="DigitalOcean token required"
)
class TestDigitalOceanExample:
    """Test DigitalOcean example (requires token)."""
    
    def test_digitalocean_example_structure(self):
        """Test that DigitalOcean example can be imported and has expected structure."""
        from examples import digitalocean
        assert hasattr(digitalocean, "main")


@pytest.mark.skipif(
    not os.environ.get("AZURE_RESOURCE_GROUP"),
    reason="Azure credentials required"
)
class TestAzureExample:
    """Test Azure example (requires Azure credentials)."""
    
    def test_azure_example_structure(self):
        """Test that Azure example can be imported and has expected structure."""
        from examples import azure
        assert hasattr(azure, "main")

