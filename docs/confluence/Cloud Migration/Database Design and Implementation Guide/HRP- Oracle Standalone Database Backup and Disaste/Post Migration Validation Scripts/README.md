# Post Migration Validation Scripts

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5323587816/Post%20Migration%20Validation%20Scripts

**Created by:** Sai Krishna Namburu on December 09, 2025  
**Last modified by:** Sai Krishna Namburu on December 09, 2025 at 11:37 AM

---

`post_rehost_oracle.sh (Oracle user tasks for database post rehost activities)`
-------------------------------------------------------------------------------

This script validates the following areas , using shell script.

|  |
| --- |
| verify\_hostname |
| check\_hosts\_file |
| backup\_hosts\_file |
| get\_current\_ip |
| update\_hosts\_file (only if the IP entry exists: update to AWS DB server IP) |
| check\_filesystem |
| check\_oratab |
| restart\_databases |
| handle\_listener |
| perform\_tnsping |
| perform\_rman\_checks |


```
#!/bin/bash
#################################################################
# Script Name : post_rehost_oracle.sh
# Description : Oracle user tasks for database post rehost activities
# Author      : Senthil Ramasamy, AWS Professional Services
# Date        : $(date +%Y-%m-%d)
# Version     : 1.0
#################################################################

# Global variables
LOG_DIR="/tmp/oracle_rehost_logs"
LOG_FILE="$LOG_DIR/Oracle_DB_Post_Rehost_$(date +%Y%m%d_%H%M%S).log"
ORATAB="/etc/oratab"
DB_PROCESSED="/tmp/db_processed_$$"
DB_STATUS="/tmp/db_status_$$"
LISTENER_STATUS="/tmp/listener_status_$$"
TNSPING_STATUS="/tmp/tnsping_status_$$"
RMAN_STATUS="/tmp/rman_status_$$"

# Function to initialize logging
setup_logging() {
    touch "$LOG_FILE"
    chmod 666 "$LOG_FILE"
    exec 1>>(tee -a "$LOG_FILE")
    exec 2>&1

    echo "#################################################################"
    echo "# Oracle Database Post-Rehost Database Activities"
    echo "# Started at: $(date)"
    echo "# Script Version: 1.0"
    echo "#################################################################"

    # Create temporary files
    touch $DB_PROCESSED $DB_STATUS $LISTENER_STATUS $TNSPING_STATUS
}

# Function to get current IP
get_current_ip() {
    #CURRENT_IP=$(ip addr show | grep 'inet ' | grep -v '*********' | awk '{print $2}' | cut -d/ -f1 | head -1)
    CURRENT_IP=`ip addr show ens5 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1`
    echo "Current IP in Oracle session: $CURRENT_IP"
    echo "=================================================================="
}

# Function to check oratab
check_oratab() {
    if [ ! -f "$ORATAB" ]; then
        echo "ERROR: Oratab file not found!"
        exit 1
    fi

    echo "Database instances found in $ORATAB:"
    grep -v '^#\|^$' "$ORATAB"
}

# Function to restart databases
# Function to restart databases
restart_databases() {
    echo "Starting database restart operations..."

    # Create a temporary file to store database entries
    local temp_db_list="/tmp/db_list_$$"
    grep -v "^#" /etc/oratab | grep -v "^$" | cut -d: -f1,2 > $temp_db_list

    while read -r db_entry
    do
        # Clear previous environment settings
        unset ORACLE_SID
        unset ORACLE_HOME

        # Extract SID and HOME
        ORACLE_SID=$(echo $db_entry | cut -d: -f1)
        ORACLE_HOME=$(echo $db_entry | cut -d: -f2)

        # Validate entries
        if [ -z "$ORACLE_SID" ] || [ -z "$ORACLE_HOME" ]; then
            echo "Skipping invalid entry: $db_entry"
            continue
        fi

        # Set Oracle environment
        export ORACLE_SID
        export ORACLE_HOME
        export PATH=$ORACLE_HOME/bin:$PATH
        export LD_LIBRARY_PATH=$ORACLE_HOME/lib

        echo "======================================================================================"
        echo "Processing database: $ORACLE_SID" | tee -a $DB_PROCESSED
        echo "Using ORACLE_HOME: $ORACLE_HOME"
        echo "Current Environment:"
        echo "ORACLE_SID=$ORACLE_SID"
        echo "ORACLE_HOME=$ORACLE_HOME"
        echo "======================================================================================"

        # Create a temporary SQL script for this database
        local tmp_sql="/tmp/restart_${ORACLE_SID}.sql"
        cat > $tmp_sql << EOF
whenever sqlerror continue
set heading off
set feedback on
set pagesize 1000
set linesize 200
set echo on

prompt Current Instance Check...
select 'Current Instance: '||sys_context('USERENV','INSTANCE_NAME') from dual;

prompt Initial Status Check for $ORACLE_SID...
select instance_name||': '||status||' - '||database_status from v\$instance;

prompt Forcing Database Shutdown...
shutdown abort;

prompt Starting up database...
startup;

prompt Verifying final status...
select instance_name||': '||status||' - '||database_status from v\$instance;

prompt Checking local_listener parameter...
show parameter local_listener

exit;
EOF

        # Execute the SQL script with explicit environment
        ORACLE_SID=$ORACLE_SID ORACLE_HOME=$ORACLE_HOME $ORACLE_HOME/bin/sqlplus -S "/ as sysdba" @$tmp_sql | tee -a $DB_STATUS

        # Cleanup temporary SQL file
        rm -f $tmp_sql

        echo "======================================================================================" | tee -a $DB_STATUS
        echo "Completed processing for database: $ORACLE_SID"
        echo "======================================================================================"
    done < $temp_db_list

    # Cleanup
    rm -f $temp_db_list
}

# Function to handle listener operations
handle_listener() {
    # Get the last valid ORACLE_HOME from oratab
    ORACLE_HOME=$(grep -v '^#\|^$' "$ORATAB" | grep -v '^$' | head -1 | cut -d: -f2)

    if [ -n "$ORACLE_HOME" ]; then
        LISTENER_ORA="$ORACLE_HOME/network/admin/listener.ora"
        if [ -f "$LISTENER_ORA" ]; then
            echo "Listener.ora content:"
            echo "======================================================================================"
            cat "$LISTENER_ORA"
            echo "========================================================================================="

            echo "Restarting listener..."
            echo "Listener Stop:" > $LISTENER_STATUS
            lsnrctl stop >> $LISTENER_STATUS
            sleep 5
            echo "Listener Start:" >>  $LISTENER_STATUS
            lsnrctl start >> $LISTENER_STATUS
            echo "Listener Status:" >>  $LISTENER_STATUS
            lsnrctl status >>  $LISTENER_STATUS
        else
            echo "WARNING: listener.ora not found at $LISTENER_ORA"
        fi
    else
        echo "ERROR: Could not determine ORACLE_HOME from oratab"
    fi
}

# Function to perform TNSPing tests
perform_tnsping() {
    echo "Performing TNSPing tests for all databases..."

    while IFS=: read -r ORACLE_SID ORACLE_HOME _
    do
        # Skip comments and empty lines
        [[ "$ORACLE_SID" =~ ^#|^$ ]] && continue
        [ -z "$ORACLE_SID" ] && continue

        echo "TNSPing test for $ORACLE_SID:" | tee -a $TNSPING_STATUS
        tnsping $ORACLE_SID | tee -a $TNSPING_STATUS
        echo "--------------------" | tee -a $TNSPING_STATUS
    done < "$ORATAB"
}

# Function to perform RMANPing tests
perform_rman_checks() {
    echo "Performing RMAN configuration checks for all databases..."
    echo "========================================================" | tee -a $RMAN_STATUS

    # Read oratab and process each database
    grep -v "^#" /etc/oratab | grep -v "^$" | cut -d: -f1,2 | while read db_entry
    do
        # Clear previous environment settings
        unset ORACLE_SID
        unset ORACLE_HOME

        # Extract SID and HOME
        ORACLE_SID=$(echo $db_entry | cut -d: -f1)
        ORACLE_HOME=$(echo $db_entry | cut -d: -f2)

        # Skip if either ORACLE_SID or ORACLE_HOME is empty
        if [ -z "$ORACLE_SID" ] || [ -z "$ORACLE_HOME" ]; then
            echo "Skipping invalid entry: $db_entry"
            continue
        fi

        # Set Oracle environment
        export ORACLE_SID
        export ORACLE_HOME
        export PATH=$ORACLE_HOME/bin:$PATH
        export LD_LIBRARY_PATH=$ORACLE_HOME/lib

        echo "======================================================================================"
        echo "Checking RMAN configuration for database: $ORACLE_SID" | tee -a $RMAN_STATUS
        echo "Using ORACLE_HOME: $ORACLE_HOME" | tee -a $RMAN_STATUS
        echo "Current Environment:"
        echo "ORACLE_SID=$ORACLE_SID"
        echo "ORACLE_HOME=$ORACLE_HOME"
        echo "======================================================================================"

        # Create temporary RMAN script
        cat > /tmp/rman_${ORACLE_SID}.rcv << EOF
CONNECT TARGET /
SHOW ALL;
EXIT;
EOF

        # Execute RMAN with explicit environment
        ORACLE_SID=$ORACLE_SID ORACLE_HOME=$ORACLE_HOME $ORACLE_HOME/bin/rman cmdfile=/tmp/rman_${ORACLE_SID}.rcv | tee -a $RMAN_STATUS

        # Cleanup temporary RMAN script
        rm -f /tmp/rman_${ORACLE_SID}.rcv

        echo "======================================================================================" | tee -a $RMAN_STATUS
        echo "Completed RMAN check for database: $ORACLE_SID" | tee -a $RMAN_STATUS
        echo "======================================================================================"

    done

    echo "RMAN configuration checks completed."
    echo "========================================================" | tee -a $RMAN_STATUS
}


# Function to generate summary
generate_summary() {
        echo ""
        echo "#################################################################"
        echo "# Oracle Database Post-Rehost Summary"
        echo "# Generated at: $(date)"
        echo "#################################################################"
        echo ""
        echo "Final Status Summary:"
        echo "===================="
        echo "1. Hostname: $(hostname)"
        echo "2. Current IP: $CURRENT_IP"
        echo ""
        echo "3. Databases Processed:"
        cat $DB_PROCESSED
        echo ""
        echo "4. Database Status:"
        cat $DB_STATUS
        echo ""
        echo "5. Listener Status:"
        cat $LISTENER_STATUS
        echo ""
        echo "6. TNSPing Results:"
        echo "-------------------------------"
        cat $TNSPING_STATUS
        echo ""
        echo "#################################################################"
        echo "# Oracle Database Post-Rehost Activities Completed"
        echo "# Ended at: $(date)"
        echo "# Log file location: $LOG_FILE"
        echo "#################################################################"
     >> "$LOG_FILE"
}

# Function to cleanup
cleanup() {
    rm -f $DB_PROCESSED $DB_STATUS $LISTENER_STATUS $TNSPING_STATUS $RMAN_STATUS
}

# Main execution
# Comment out any function you don't want to run
main() {
    setup_logging
    get_current_ip
    check_oratab
    restart_databases
    handle_listener
    perform_tnsping
    perform_rman_checks
    generate_summary
    cleanup
}

# Execute main function
main
```


`post_rehost_root.sh (Root tasks for Oracle database post rehost activities (run as ssm user or any use which has sudo access to root)`
---------------------------------------------------------------------------------------------------------------------------------------


```
#!/bin/bash
###############################################################################################################################
# Script Name : post_rehost_root.sh
# Description : Root tasks for Oracle database post rehost activities (run as ssm user or any use which has sudo access to root)
# Author      : Senthil Ramasamy, AWS Professional Services
# Date        : $(date +%Y-%m-%d)
# Version     : 1.0
###############################################################################################################################

# Global variables
LOG_DIR="/tmp/oracle_rehost_logs"
LOG_FILE=""
HOSTNAME=""
CURRENT_IP=""
BACKUP_FILE=""

# Function to check if script is run as root
check_user() {
    if [ "$(id -u)" -eq 0 ]; then
        echo "Please run this script as a regular user, not as root"
        exit 1
    fi
}

# Function to setup logging
setup_logging() {
    LOG_FILE="$LOG_DIR/Oracle_DB_Post_Rehost_$(date +%Y%m%d_%H%M%S).log"
    sudo mkdir -p $LOG_DIR
    sudo chmod 777 $LOG_DIR
    touch "$LOG_FILE"
    chmod 666 "$LOG_FILE"
    exec 1>>(tee -a "$LOG_FILE")
    exec 2>&1

    echo "#################################################################"
    echo "# Oracle Database Post-Rehost Root Activities"
    echo "# Started at: $(date)"
    echo "# Script Version: 1.0"
    echo "#################################################################"
}

# Function to check command status
check_status() {
    if [ $? -eq 0 ]; then
        echo "SUCCESS: $1"
    else
        echo "ERROR: $1"
        exit 1
    fi
}

# Function to verify hostname
verify_hostname() {
    HOSTNAME=$(hostname)
    echo "Current Hostname: $HOSTNAME"
    check_status "Hostname verification"
    echo "================================================================"
}

# Function to check hosts file
check_hosts_file() {
    echo "Checking /etc/hosts file..."
    cat /etc/hosts
    check_status "Hosts file check"
    echo "================================================================"
}

# Function to backup hosts file
backup_hosts_file() {
    BACKUP_FILE="/etc/hosts_$(date +%Y%m%d)"
    cp -p /etc/hosts "$BACKUP_FILE"
    check_status "Hosts file backup created: $BACKUP_FILE"
    echo "================================================================"
}

# Function to get current IP
get_current_ip() {
    CURRENT_IP=$(ip addr show ens5 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1)
    echo "Current IP ON AWS: $CURRENT_IP"
}

# Function to update hosts file
update_hosts_file() {
    echo "Updating IP address in hosts file..."
    TEMP_HOSTS=$(mktemp)

    while IFS= read -r line; do
        if echo "$line" | grep -q "$HOSTNAME"; then
            existing_names=$(echo "$line" | awk '{$1=""; print $0}')
            echo "$CURRENT_IP $existing_names" >> "$TEMP_HOSTS"
        else
            echo "$line" >> "$TEMP_HOSTS"
        fi
    done < /etc/hosts

    mv "$TEMP_HOSTS" /etc/hosts
    chmod 644 /etc/hosts
    check_status "Hosts file IP update"

    echo "Updated /etc/hosts content:"
    cat /etc/hosts
    echo "================================================================"
}

# Function to check filesystem
check_filesystem() {
    echo "Checking filesystem..."
    df -Ph
    check_status "Filesystem check"
    echo "================================================================"
}

# Function to perform root tasks
perform_root_tasks() {
    sudo su - << EOF_ROOT
    $(declare -f check_status)
    $(declare -f verify_hostname)
    $(declare -f check_hosts_file)
    $(declare -f backup_hosts_file)
    $(declare -f get_current_ip)
    $(declare -f update_hosts_file)
    $(declare -f check_filesystem)

    verify_hostname
    check_hosts_file
    backup_hosts_file
    get_current_ip
    update_hosts_file
    check_filesystem

    exit # Exit from root shell
EOF_ROOT
}

# Function to print completion message
print_completion() {
    echo "#################################################################"
    echo "# Root activities completed"
    echo "# Ended at: $(date)"
    echo "# Log file location: $LOG_FILE"
    echo "#################################################################"
}

# Main execution
main() {
    check_user
    setup_logging
    perform_root_tasks
    print_completion
}

# Execute main function
main
```


Sample Log Output