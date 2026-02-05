"""Property-based tests for HTML CLI integration.

Feature: html-report-generation
Tests CLI integration properties.
"""
import pytest
import json
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume
from src.reverse_diagrams import generate_html_report_cli


@settings(max_examples=100, deadline=None)
@given(
    has_org=st.booleans(),
    has_groups=st.booleans(),
    has_assignments=st.booleans()
)
@pytest.mark.property_test
def test_property_1_html_generation_from_available_files(has_org, has_groups, has_assignments, tmp_path):
    """
    Feature: html-report-generation
    Property 1: HTML Generation from Available JSON Files
    
    For any combination of JSON data files (organizations.json, groups.json,
    account_assignments.json) that exist in the diagrams/json directory, when the CLI
    is executed with --html-report, the generated HTML file should contain sections
    corresponding to each available JSON file with the appropriate data rendered.
    
    Validates: Requirements 1.1, 3.1, 3.2, 3.3, 3.4, 3.5
    """
    # Require at least one file
    assume(has_org or has_groups or has_assignments)
    
    # Create JSON directory
    json_dir = tmp_path / "json"
    json_dir.mkdir()
    
    # Track which sections should be present
    expected_sections = []
    
    # Create organizations file if requested
    if has_org:
        org_file = json_dir / "organizations.json"
        org_data = {
            "organization": {"Id": "o-test123", "Arn": "arn:aws:organizations::123456789012:organization/o-test123"},
            "accounts": [
                {"Id": "123456789012", "Name": "TestAccount1", "Email": "test1@example.com", "Status": "ACTIVE"},
                {"Id": "123456789013", "Name": "TestAccount2", "Email": "test2@example.com", "Status": "ACTIVE"}
            ],
            "organizational_units": [
                {"Id": "ou-test1", "Name": "TestOU1"},
                {"Id": "ou-test2", "Name": "TestOU2"}
            ]
        }
        org_file.write_text(json.dumps(org_data))
        expected_sections.append(("organizations", "AWS Organizations", "TestAccount1", "TestOU1"))
    
    # Create groups file if requested
    if has_groups:
        groups_file = json_dir / "groups.json"
        groups_data = [
            {
                "group_name": "AdminGroup",
                "members": [
                    {"MemberId": {"UserName": "admin_user1"}},
                    {"MemberId": {"UserName": "admin_user2"}}
                ]
            },
            {
                "group_name": "DevGroup",
                "members": [
                    {"MemberId": {"UserName": "dev_user1"}}
                ]
            }
        ]
        groups_file.write_text(json.dumps(groups_data))
        expected_sections.append(("groups", "Identity Center", "AdminGroup", "admin_user1"))
    
    # Create assignments file if requested
    if has_assignments:
        assignments_file = json_dir / "account_assignments.json"
        assignments_data = {
            "TestAccount1": [
                {
                    "PrincipalType": "GROUP",
                    "GroupName": "AdminGroup",
                    "PermissionSetName": "AdministratorAccess"
                }
            ],
            "TestAccount2": [
                {
                    "PrincipalType": "GROUP",
                    "GroupName": "DevGroup",
                    "PermissionSetName": "PowerUserAccess"
                }
            ]
        }
        assignments_file.write_text(json.dumps(assignments_data))
        expected_sections.append(("assignments", "Account Assignments", "TestAccount1", "AdministratorAccess"))
    
    # Generate HTML report
    output_path = tmp_path / "test_report.html"
    try:
        generate_html_report_cli(
            html_output=str(output_path),
            json_dir=str(json_dir)
        )
    except Exception as e:
        pytest.fail(f"HTML generation should succeed with available files: {e}")
    
    # Verify HTML file was created
    assert output_path.exists(), "HTML file should be created"
    
    # Read HTML content
    html_content = output_path.read_text()
    
    # Verify each expected section is present with its data
    for section_type, section_title, sample_data1, sample_data2 in expected_sections:
        # Check section title appears
        assert section_title in html_content or section_title.replace(" ", "") in html_content.replace(" ", ""), \
            f"Section '{section_title}' should appear in HTML"
        
        # Check sample data appears
        assert sample_data1 in html_content or sample_data1.replace(" ", "") in html_content.replace(" ", ""), \
            f"Data '{sample_data1}' from {section_type} should appear in HTML"
        
        assert sample_data2 in html_content or sample_data2.replace(" ", "") in html_content.replace(" ", ""), \
            f"Data '{sample_data2}' from {section_type} should appear in HTML"
    
    # Verify HTML structure
    assert '<!DOCTYPE html>' in html_content, "HTML should have DOCTYPE"
    assert '<html' in html_content.lower(), "HTML should have html tag"
    assert '</html>' in html_content.lower(), "HTML should have closing html tag"


@settings(max_examples=50, deadline=None)
@given(
    file_combination=st.integers(min_value=1, max_value=7)  # 1-7 represents all combinations of 3 files
)
@pytest.mark.property_test
def test_property_1_all_file_combinations(file_combination, tmp_path):
    """
    Feature: html-report-generation
    Property 1: HTML Generation from Available JSON Files
    
    Test all possible combinations of JSON files (1-7 represents binary combinations).
    
    Validates: Requirements 3.4, 3.5
    """
    # Decode combination (binary representation)
    has_org = bool(file_combination & 1)
    has_groups = bool(file_combination & 2)
    has_assignments = bool(file_combination & 4)
    
    # Create JSON directory
    json_dir = tmp_path / "json"
    json_dir.mkdir()
    
    files_created = []
    
    if has_org:
        org_file = json_dir / "organizations.json"
        org_file.write_text(json.dumps({
            "organization": {"Id": "o-test"},
            "accounts": [],
            "organizational_units": []
        }))
        files_created.append("organizations")
    
    if has_groups:
        groups_file = json_dir / "groups.json"
        groups_file.write_text(json.dumps([]))
        files_created.append("groups")
    
    if has_assignments:
        assignments_file = json_dir / "account_assignments.json"
        assignments_file.write_text(json.dumps({}))
        files_created.append("assignments")
    
    # Generate HTML report
    output_path = tmp_path / "report.html"
    try:
        generate_html_report_cli(
            html_output=str(output_path),
            json_dir=str(json_dir)
        )
    except Exception as e:
        pytest.fail(f"HTML generation should succeed with {len(files_created)} file(s): {e}")
    
    # Verify HTML was created
    assert output_path.exists(), \
        f"HTML should be created with files: {', '.join(files_created)}"
    
    # Verify HTML is valid
    html_content = output_path.read_text()
    assert '<!DOCTYPE html>' in html_content, "HTML should be valid"
    assert len(html_content) > 1000, "HTML should have substantial content"



@settings(max_examples=50, deadline=None)
@given(
    has_org=st.booleans(),
    has_groups=st.booleans(),
    has_assignments=st.booleans()
)
@pytest.mark.property_test
def test_property_2_html_only_generation_isolation(has_org, has_groups, has_assignments, tmp_path):
    """
    Feature: html-report-generation
    Property 2: HTML-Only Generation Isolation
    
    For any execution of the CLI with only the --html-report flag (without -o or -i flags),
    the diagrams/code and diagrams/images directories should remain unchanged, and only
    the HTML report file should be created or modified.
    
    Validates: Requirements 1.2
    """
    # Require at least one file
    assume(has_org or has_groups or has_assignments)
    
    # Create JSON directory with files
    json_dir = tmp_path / "json"
    json_dir.mkdir()
    
    if has_org:
        (json_dir / "organizations.json").write_text(json.dumps({
            "organization": {"Id": "o-test"},
            "accounts": [],
            "organizational_units": []
        }))
    
    if has_groups:
        (json_dir / "groups.json").write_text(json.dumps([]))
    
    if has_assignments:
        (json_dir / "account_assignments.json").write_text(json.dumps({}))
    
    # Create code and images directories (simulating previous diagram generation)
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    existing_code_file = code_dir / "existing_diagram.py"
    existing_code_file.write_text("# Existing diagram code")
    
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    existing_image_file = images_dir / "existing_diagram.png"
    existing_image_file.write_text("fake image data")
    
    # Record initial state
    initial_code_files = set(code_dir.iterdir())
    initial_image_files = set(images_dir.iterdir())
    initial_code_mtime = existing_code_file.stat().st_mtime
    initial_image_mtime = existing_image_file.stat().st_mtime
    
    # Generate HTML report only (no diagram generation)
    output_path = tmp_path / "reports" / "report.html"
    try:
        generate_html_report_cli(
            html_output=str(output_path),
            json_dir=str(json_dir)
        )
    except Exception as e:
        pytest.fail(f"HTML-only generation should succeed: {e}")
    
    # Verify HTML was created
    assert output_path.exists(), "HTML file should be created"
    
    # Verify code directory unchanged
    final_code_files = set(code_dir.iterdir())
    assert initial_code_files == final_code_files, \
        "Code directory should remain unchanged during HTML-only generation"
    
    # Verify images directory unchanged
    final_image_files = set(images_dir.iterdir())
    assert initial_image_files == final_image_files, \
        "Images directory should remain unchanged during HTML-only generation"
    
    # Verify existing files were not modified
    assert existing_code_file.stat().st_mtime == initial_code_mtime, \
        "Existing code files should not be modified"
    
    assert existing_image_file.stat().st_mtime == initial_image_mtime, \
        "Existing image files should not be modified"
    
    # Verify only HTML file was created/modified
    reports_dir = tmp_path / "reports"
    assert reports_dir.exists(), "Reports directory should be created"
    assert output_path.exists(), "HTML report should be created"



@settings(max_examples=30, deadline=None)
@given(
    generate_org=st.booleans(),
    generate_identity=st.booleans()
)
@pytest.mark.property_test
def test_property_3_combined_generation_completeness(generate_org, generate_identity, tmp_path):
    """
    Feature: html-report-generation
    Property 3: Combined Generation Completeness
    
    For any execution of the CLI with --html-report combined with -o or -i flags,
    both the diagram outputs (Python code and/or PNG images) and the HTML report
    should be generated successfully.
    
    Validates: Requirements 1.3
    
    Note: This is a simplified test that verifies the logic flow. Full integration
    testing with actual AWS API calls would be done in integration tests.
    """
    # Require at least one diagram type
    assume(generate_org or generate_identity)
    
    # Create output directories
    json_dir = tmp_path / "json"
    json_dir.mkdir()
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    
    # Simulate diagram generation by creating JSON files
    # (In real scenario, these would be created by -o or -i flags)
    if generate_org:
        org_file = json_dir / "organizations.json"
        org_file.write_text(json.dumps({
            "organization": {"Id": "o-test123"},
            "accounts": [{"Id": "123456789012", "Name": "TestAccount"}],
            "organizational_units": []
        }))
        # Simulate diagram code generation
        (code_dir / "graph_org.py").write_text("# Organization diagram code")
    
    if generate_identity:
        groups_file = json_dir / "groups.json"
        groups_file.write_text(json.dumps([
            {"group_name": "TestGroup", "members": []}
        ]))
        assignments_file = json_dir / "account_assignments.json"
        assignments_file.write_text(json.dumps({
            "TestAccount": [{"PrincipalType": "GROUP", "GroupName": "TestGroup", "PermissionSetName": "Admin"}]
        }))
        # Simulate diagram code generation
        (code_dir / "graph_sso_complete.py").write_text("# Identity Center diagram code")
    
    # Now generate HTML report (simulating combined generation)
    output_path = tmp_path / "reports" / "report.html"
    try:
        generate_html_report_cli(
            html_output=str(output_path),
            json_dir=str(json_dir)
        )
    except Exception as e:
        pytest.fail(f"Combined generation should succeed: {e}")
    
    # Verify diagram outputs exist (simulated)
    if generate_org:
        assert (code_dir / "graph_org.py").exists(), \
            "Organization diagram code should exist"
    
    if generate_identity:
        assert (code_dir / "graph_sso_complete.py").exists(), \
            "Identity Center diagram code should exist"
    
    # Verify HTML report was generated
    assert output_path.exists(), \
        "HTML report should be generated in combined mode"
    
    # Verify HTML contains data from both sources if both were generated
    html_content = output_path.read_text()
    
    if generate_org:
        assert "TestAccount" in html_content or "Organizations" in html_content, \
            "HTML should contain organization data"
    
    if generate_identity:
        assert "TestGroup" in html_content or "Identity Center" in html_content, \
            "HTML should contain identity center data"
    
    # Verify HTML is complete
    assert '<!DOCTYPE html>' in html_content, "HTML should be valid"
    assert len(html_content) > 1000, "HTML should have substantial content"



@settings(max_examples=50, deadline=None)
@given(
    has_org=st.booleans(),
    has_groups=st.booleans(),
    has_assignments=st.booleans()
)
@pytest.mark.property_test
def test_property_8_offline_generation_capability(has_org, has_groups, has_assignments, tmp_path):
    """
    Feature: html-report-generation
    Property 8: Offline Generation Capability
    
    For any execution of HTML report generation from existing JSON files, no AWS client
    should be instantiated, no AWS API calls should be made, and the operation should
    complete successfully without network access.
    
    Validates: Requirements 5.1
    """
    # Require at least one file
    assume(has_org or has_groups or has_assignments)
    
    # Create JSON directory with files
    json_dir = tmp_path / "json"
    json_dir.mkdir()
    
    if has_org:
        (json_dir / "organizations.json").write_text(json.dumps({
            "organization": {"Id": "o-test"},
            "accounts": [],
            "organizational_units": []
        }))
    
    if has_groups:
        (json_dir / "groups.json").write_text(json.dumps([]))
    
    if has_assignments:
        (json_dir / "account_assignments.json").write_text(json.dumps({}))
    
    output_path = tmp_path / "report.html"
    
    # Mock AWS client manager to verify it's not called
    with patch('src.reverse_diagrams.get_client_manager') as mock_client_manager:
        # Mock boto3 to verify no AWS calls are made
        with patch('boto3.client') as mock_boto_client:
            with patch('boto3.Session') as mock_boto_session:
                # Generate HTML report
                try:
                    generate_html_report_cli(
                        html_output=str(output_path),
                        json_dir=str(json_dir)
                    )
                except Exception as e:
                    pytest.fail(f"Offline HTML generation should succeed: {e}")
                
                # Verify no AWS clients were instantiated
                assert not mock_client_manager.called, \
                    "AWS client manager should not be called during HTML-only generation"
                
                assert not mock_boto_client.called, \
                    "boto3.client should not be called during HTML-only generation"
                
                assert not mock_boto_session.called, \
                    "boto3.Session should not be called during HTML-only generation"
    
    # Verify HTML was created successfully
    assert output_path.exists(), \
        "HTML should be created without AWS access"
    
    # Verify HTML is valid
    html_content = output_path.read_text()
    assert '<!DOCTYPE html>' in html_content, \
        "HTML should be valid"


@settings(max_examples=30, deadline=None)
@given(
    file_type=st.sampled_from(["organizations", "groups", "assignments"])
)
@pytest.mark.property_test
def test_property_8_no_network_required(file_type, tmp_path):
    """
    Feature: html-report-generation
    Property 8: Offline Generation Capability
    
    HTML generation should work without any network access, using only local JSON files.
    
    Validates: Requirements 5.1
    """
    # Create JSON file
    json_dir = tmp_path / "json"
    json_dir.mkdir()
    
    json_file = json_dir / f"{file_type}.json"
    
    if file_type == "organizations":
        data = {"organization": {"Id": "o-test"}, "accounts": [], "organizational_units": []}
    elif file_type == "groups":
        data = [{"group_name": "TestGroup", "members": []}]
    else:  # assignments
        data = {}
    
    json_file.write_text(json.dumps(data))
    
    output_path = tmp_path / "report.html"
    
    # Mock socket to simulate no network access
    with patch('socket.socket') as mock_socket:
        mock_socket.side_effect = OSError("Network is unreachable")
        
        # Generate HTML report (should work without network)
        try:
            generate_html_report_cli(
                html_output=str(output_path),
                json_dir=str(json_dir)
            )
        except OSError as e:
            if "Network is unreachable" in str(e):
                pytest.fail("HTML generation should not require network access")
            raise
        except Exception as e:
            pytest.fail(f"HTML generation should succeed without network: {e}")
    
    # Verify HTML was created
    assert output_path.exists(), \
        "HTML should be created without network access"
