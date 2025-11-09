#!/usr/bin/env python3
"""
Integration test for FAT prototype - verifies all components work together
WITHOUT requiring a running Perspective session or AI API key
"""

import sys
from pathlib import Path

print("=" * 60)
print("FAT Prototype Integration Test")
print("=" * 60)
print()

# Test 1: Import all new components
print("Test 1: Importing new FAT components...")
try:
    from ignition_toolkit.playbook.models import StepType
    from ignition_toolkit.playbook.executors import (
        PerspectiveDiscoverPageHandler,
        PerspectiveExtractMetadataHandler,
        PerspectiveExecuteTestManifestHandler,
        AIAnalyzePageStructureHandler,
        AIGenerateTestCasesHandler,
        FATGenerateReportHandler,
    )
    from ignition_toolkit.ai.assistant import AIAssistant
    from ignition_toolkit.storage.models import FATReportModel, FATComponentTestModel
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Verify new step types exist
print("\nTest 2: Verifying new step types...")
required_types = [
    'PERSPECTIVE_DISCOVER_PAGE',
    'PERSPECTIVE_EXTRACT_METADATA',
    'PERSPECTIVE_EXECUTE_TEST_MANIFEST',
    'AI_ANALYZE_PAGE_STRUCTURE',
    'AI_GENERATE_TEST_CASES',
    'FAT_GENERATE_REPORT',
]
missing = []
for step_type in required_types:
    if not hasattr(StepType, step_type):
        missing.append(step_type)

if missing:
    print(f"❌ Missing step types: {', '.join(missing)}")
    sys.exit(1)
else:
    print(f"✅ All {len(required_types)} new step types registered")

# Test 3: Verify AI assistant has new methods
print("\nTest 3: Verifying AI assistant extensions...")
assistant = AIAssistant()  # No API key = fallback mode
required_methods = [
    'analyze_page_for_fat',
    'generate_fat_test_cases',
    'verify_visual_consistency',
]
missing_methods = []
for method in required_methods:
    if not hasattr(assistant, method) or not callable(getattr(assistant, method)):
        missing_methods.append(method)

if missing_methods:
    print(f"❌ Missing AI methods: {', '.join(missing_methods)}")
    sys.exit(1)
else:
    print(f"✅ All {len(required_methods)} AI methods available")

# Test 4: Verify playbooks load correctly
print("\nTest 4: Loading FAT playbooks...")
import yaml

playbooks = [
    'playbooks/perspective/fat_basic_test.yaml',
    'playbooks/perspective/fat_comprehensive_test.yaml',
]

for playbook_path in playbooks:
    try:
        with open(playbook_path, 'r') as f:
            data = yaml.safe_load(f)

        # Validate required fields
        assert 'name' in data, "Missing 'name' field"
        assert 'steps' in data, "Missing 'steps' field"
        assert 'parameters' in data, "Missing 'parameters' field"
        assert 'domain' in data, "Missing 'domain' field"
        assert data['domain'] == 'perspective', "Wrong domain"

        step_count = len(data['steps'])
        print(f"  ✅ {Path(playbook_path).name}: {step_count} steps")

    except Exception as e:
        print(f"  ❌ {Path(playbook_path).name}: {e}")
        sys.exit(1)

# Test 5: Verify backward compatibility
print("\nTest 5: Checking backward compatibility...")
try:
    # Import existing executors
    from ignition_toolkit.playbook.executors import (
        GatewayLoginHandler,
        BrowserNavigateHandler,
        DesignerLaunchHandler,
        UtilityLogHandler,
    )

    # Verify old step types still exist
    old_types = [
        'GATEWAY_LOGIN',
        'BROWSER_NAVIGATE',
        'DESIGNER_LAUNCH',
        'UTILITY_LOG',
    ]
    for step_type in old_types:
        assert hasattr(StepType, step_type), f"Missing old step type: {step_type}"

    print("✅ All existing handlers and step types intact")

except Exception as e:
    print(f"❌ Backward compatibility issue: {e}")
    sys.exit(1)

# Test 6: Verify JavaScript discovery script exists and is valid
print("\nTest 6: Checking JavaScript component discovery...")
js_path = Path('ignition_toolkit/browser/component_discovery.js')
if not js_path.exists():
    print(f"❌ JavaScript file not found: {js_path}")
    sys.exit(1)

js_content = js_path.read_text()
if 'discoverPerspectiveComponents' not in js_content:
    print("❌ Main function not found in JavaScript")
    sys.exit(1)

if 'Shadow DOM' not in js_content:
    print("⚠️  Warning: Shadow DOM handling might be missing")

print(f"✅ JavaScript discovery script valid ({len(js_content)} bytes)")

# Test 7: Test AI fallback logic (without API key)
print("\nTest 7: Testing AI fallback logic...")
try:
    import asyncio

    async def test_fallback():
        assistant = AIAssistant()  # No API key

        # Test generate_fat_test_cases with fallback
        result = await assistant.generate_fat_test_cases(
            components=[
                {"id": "btn1", "type": "button", "selector": "#btn1"},
                {"id": "input1", "type": "input", "selector": "#input1"},
            ],
            mode="comprehensive"
        )

        # Should return fallback plan
        assert result.metadata.get("test_plan") is not None, "No test plan generated"
        assert len(result.metadata["test_plan"]) > 0, "Empty test plan"

        return result

    result = asyncio.run(test_fallback())
    print(f"✅ AI fallback working ({len(result.metadata['test_plan'])} tests generated)")

except Exception as e:
    print(f"❌ AI fallback test failed: {e}")
    sys.exit(1)

# Test 8: Verify database models are properly defined
print("\nTest 8: Checking database models...")
try:
    # Check FATReportModel
    assert hasattr(FATReportModel, '__tablename__')
    assert FATReportModel.__tablename__ == 'fat_reports'

    # Check FATComponentTestModel
    assert hasattr(FATComponentTestModel, '__tablename__')
    assert FATComponentTestModel.__tablename__ == 'fat_component_tests'

    # Check relationships
    assert hasattr(FATReportModel, 'component_tests')
    assert hasattr(FATComponentTestModel, 'report')

    print("✅ Database models properly defined")

except Exception as e:
    print(f"❌ Database model issue: {e}")
    sys.exit(1)

# Summary
print("\n" + "=" * 60)
print("✅ ALL INTEGRATION TESTS PASSED")
print("=" * 60)
print()
print("Prototype Status: READY FOR MANUAL TESTING")
print()
print("Next Steps:")
print("1. Start Ignition Gateway with Perspective")
print("2. Start toolkit server: ignition-toolkit serve")
print("3. Open frontend: http://localhost:9000")
print("4. Navigate to Playbooks → perspective/fat_basic_test.yaml")
print("5. Fill in your Perspective URL")
print("6. Run and review generated report!")
print()
print("Note: Database migration needed for FAT report persistence")
print("      (Reports still generated as HTML files)")
print("=" * 60)
