# Proboscis Build Script
# ======================
#
# Runs nosetests, executes example runner, and generates documentation.
#

function run_nose() {
    nosetests --with-coverage $@
}
function run_py() {
    coverage run --source=proboscis $@
}

set -e
coverage erase

echo 'Running example tests...'
run_py run_tests.py


echo 'Running unit tests...'
run_nose tests.unit.test_asserts
run_nose tests.unit.test_sorting
run_nose tests.unit.test_check
run_nose tests.unit.test_core



#jython tests/proboscis_test.py

#ipy tests/proboscis_test.py



# We'll later run these tests as part of build_sphinx, but if anything fails
# it's easier to see when run by itself.

echo "Creating HTML coverage report..."
coverage html -d covhtml -i


echo 'Building docs...'
python setup.py build_sphinx


echo 'SUCCESS!'
