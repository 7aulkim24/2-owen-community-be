#!/bin/sh
# usage: ./wait-for-it.sh host:port -- command args
# example: ./wait-for-it.sh db:3306 -- uvicorn main:app

set -e

hostport="$1"
shift

host=$(echo $hostport | cut -d : -f 1)
port=$(echo $hostport | cut -d : -f 2)

echo "Waiting for $host:$port..."

# Loop until we can connect to the host:port
until nc -z "$host" "$port"; do
  echo "Waiting for database connection at $host:$port..."
  sleep 2
done

echo "Database is up!"

# If the next argument is '--', shift it
if [ "$1" = "--" ]; then
    shift
fi

# Execute the command
exec "$@"
