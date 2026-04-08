# Dockerfile untuk Odoo 17 dengan PKS Pabrik Module
# =================================================

FROM odoo:17.0

LABEL maintainer="PT. Sawit Nusantara <it@sawitnusantara.co.id>"
LABEL description="Odoo 17 dengan Modul PKS Pabrik"

USER root

# Install dependencies tambahan
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    python3-dev \
    libxml2-dev \
    libxslt1-dev \
    libldap2-dev \
    libsasl2-dev \
    libtiff5-dev \
    libjpeg62-turbo-dev \
    libopenjp2-7-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libxcb1-dev \
    libpq-dev \
    git \
    wget \
    curl \
    vim \
    nano \
    htop \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages tambahan
RUN pip3 install --no-cache-dir \
    pandas \
    numpy \
    openpyxl \
    xlrd \
    xlwt \
    requests \
    redis \
    celery \
    flower \
    gunicorn \
    psycopg2-binary \
    sentry-sdk \
    newrelic

# Copy custom Odoo configuration
COPY ./odoo.conf /etc/odoo/odoo.conf

# Copy PKS Pabrik module
COPY ./pks_pabrik /mnt/extra-addons/pks_pabrik

# Set permissions
RUN chown -R odoo:odoo /mnt/extra-addons \
    && chmod -R 755 /mnt/extra-addons \
    && chown odoo:odoo /etc/odoo/odoo.conf

# Create directories for filestore and sessions
RUN mkdir -p /var/lib/odoo/filestore \
    && mkdir -p /var/lib/odoo/sessions \
    && chown -R odoo:odoo /var/lib/odoo

# Expose ports
EXPOSE 8069 8071 8072

# Switch to odoo user
USER odoo

# Set environment variables
ENV ODOO_RC /etc/odoo/odoo.conf
ENV ODOO_ADDONS_PATH /mnt/extra-addons

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8069/web/health || exit 1

# Default command
CMD ["odoo"]
