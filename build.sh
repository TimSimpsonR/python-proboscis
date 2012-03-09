# Proboscis Build Script
# ======================
#
# Runs nosetests, executes example runner, and generates documentation.
#
set -e
echo 'Running unit tests...'
nosetests tests.proboscis_test
nosetests tests.proboscis_check_test

# We'll later run these tests as part of build_sphinx, but if anything fails
# it's easier to see when run by itself.
echo 'Running example tests...'
python run_tests.py
echo 'Building docs...'
python setup.py build_sphinx
echo 'SUCCESS!'
