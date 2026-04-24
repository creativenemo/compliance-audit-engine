FROM public.ecr.aws/lambda/python:3.12

# Install Playwright system dependencies
RUN dnf install -y \
    atk \
    cups-libs \
    dbus-libs \
    libX11 \
    libXcomposite \
    libXcursor \
    libXdamage \
    libXext \
    libXfixes \
    libXi \
    libXrandr \
    libXrender \
    libXtst \
    libxcb \
    libxkbcommon \
    mesa-libgbm \
    nss \
    pango \
    xorg-x11-fonts-100dpi \
    xorg-x11-fonts-75dpi \
    xorg-x11-fonts-cyrillic \
    xorg-x11-fonts-misc \
    xorg-x11-fonts-Type1 \
    xorg-x11-utils \
    && dnf clean all

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (Chromium only)
RUN python -m playwright install chromium

COPY app/ ${LAMBDA_TASK_ROOT}/app/
COPY orchestrator/ ${LAMBDA_TASK_ROOT}/orchestrator/
COPY scrapers/ ${LAMBDA_TASK_ROOT}/scrapers/
COPY index_refresher/ ${LAMBDA_TASK_ROOT}/index_refresher/

CMD ["app.main.handler"]
