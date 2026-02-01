#!/usr/bin/env bats

# Test the macsetup bash wrapper script

setup() {
    # Get the directory of this test file
    BATS_TEST_DIRNAME="$(cd "$(dirname "$BATS_TEST_FILENAME")" && pwd)"
    # Navigate to project root
    PROJECT_ROOT="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    WRAPPER="${PROJECT_ROOT}/bin/macsetup"
}

@test "wrapper script exists and is executable" {
    [ -f "$WRAPPER" ]
    [ -x "$WRAPPER" ]
}

@test "wrapper shows version" {
    run "$WRAPPER" --version
    [ "$status" -eq 0 ]
    [[ "$output" =~ "macsetup" ]]
    [[ "$output" =~ [0-9]+\.[0-9]+\.[0-9]+ ]]
}

@test "wrapper shows help with no arguments" {
    run "$WRAPPER"
    [ "$status" -eq 0 ]
    [[ "$output" =~ "usage:" ]] || [[ "$output" =~ "macOS Configuration Sync CLI" ]]
}

@test "wrapper shows help with --help flag" {
    run "$WRAPPER" --help
    [ "$status" -eq 0 ]
    [[ "$output" =~ "capture" ]]
    [[ "$output" =~ "setup" ]]
    [[ "$output" =~ "preview" ]]
}

@test "wrapper accepts capture subcommand" {
    run "$WRAPPER" capture --help
    [ "$status" -eq 0 ]
    [[ "$output" =~ "--profile" ]]
}

@test "wrapper accepts setup subcommand" {
    run "$WRAPPER" setup --help
    [ "$status" -eq 0 ]
    [[ "$output" =~ "--resume" ]]
}

@test "wrapper accepts preview subcommand" {
    run "$WRAPPER" preview --help
    [ "$status" -eq 0 ]
    [[ "$output" =~ "--diff" ]]
}

@test "wrapper accepts sync subcommand" {
    run "$WRAPPER" sync --help
    [ "$status" -eq 0 ]
    [[ "$output" =~ "start" ]]
    [[ "$output" =~ "stop" ]]
}

@test "wrapper accepts profile subcommand" {
    run "$WRAPPER" profile --help
    [ "$status" -eq 0 ]
    [[ "$output" =~ "list" ]]
    [[ "$output" =~ "create" ]]
}

@test "wrapper accepts validate subcommand" {
    run "$WRAPPER" validate --help
    [ "$status" -eq 0 ]
    [[ "$output" =~ "--strict" ]]
}

@test "wrapper accepts global --json flag" {
    run "$WRAPPER" --help
    [ "$status" -eq 0 ]
    [[ "$output" =~ "--json" ]]
}

@test "wrapper accepts global --quiet flag" {
    run "$WRAPPER" --help
    [ "$status" -eq 0 ]
    [[ "$output" =~ "--quiet" ]]
}

@test "wrapper accepts global --verbose flag" {
    run "$WRAPPER" --help
    [ "$status" -eq 0 ]
    [[ "$output" =~ "--verbose" ]]
}

@test "wrapper accepts global --config-dir flag" {
    run "$WRAPPER" --help
    [ "$status" -eq 0 ]
    [[ "$output" =~ "--config-dir" ]]
}
