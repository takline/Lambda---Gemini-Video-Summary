FROM public.ecr.aws/lambda/python:3.12

RUN dnf -y install make automake git rpm tar gcc gcc-c++ kernel-devel cmake autoconf libtool pkgconfig wget libcurl-devel unzip nasm freetype-devel

##Docker stuff

# Setup build dir for libav
RUN mkdir ~/ffmpeg_sources
RUN mkdir $HOME/ffmpeg_build


# x264 - a free software library and application for encoding video streams into
# the H.264/MPEG-4 AVC compression format, and is released under the terms of
# the GNU GPL.
WORKDIR ~/ffmpeg_sources
RUN git clone --depth 1 https://code.videolan.org/videolan/x264.git
WORKDIR x264
RUN PKG_CONFIG_PATH="$HOME/ffmpeg_build/lib/pkgconfig" \
./configure \
--prefix="$HOME/ffmpeg_build" \
--bindir="$HOME/bin" \
--disable-asm \
--enable-static \
&& make && make install && make distclean

# x265 - a H.265 / HEVC video encoder application library, designed to encode
# video or images into an H.265 / HEVC encoded bitstream.
WORKDIR ~/ffmpeg_sources
RUN git clone --depth 1 https://github.com/videolan/x265.git
WORKDIR x265/build/linux
RUN cmake -G "Unix Makefiles" \
-DCMAKE_INSTALL_PREFIX="$HOME/ffmpeg_build" \
-DENABLE_SHARED:bool=off ../../source \
&& make && make install

# fdk-aac - A standalone library of the Fraunhofer FDK AAC code from Android.
WORKDIR ~/ffmpeg_sources
RUN git clone --depth 1 https://github.com/mstorsjo/fdk-aac.git
WORKDIR fdk-aac
RUN autoreconf -fiv \
&& ./configure \
--prefix="$HOME/ffmpeg_build" \
--disable-shared \
&& make && make install && make distclean


WORKDIR ~/ffmpeg_sources
RUN rm -rf /opt/yasm*
RUN curl -L -O  http://www.tortall.net/projects/yasm/releases/yasm-1.3.0.tar.gz
RUN tar xzfv yasm-1.3.0.tar.gz && rm -f yasm-1.3.0.tar.gz
WORKDIR yasm-1.3.0
RUN ./configure \
--prefix="$HOME/ffmpeg_build" \
--bindir="$HOME/bin" \
&& make && make install && make distclean && export "PATH=$PATH:$HOME/bin" 

# LAME - a high quality MPEG Audio Layer III (MP3) encoder licensed under the
# LGPL.
WORKDIR ~/ffmpeg_sources
RUN curl -L -O https://sourceforge.net/projects/lame/files/lame/3.100/lame-3.100.tar.gz
RUN tar xzvf lame-3.100.tar.gz
WORKDIR lame-3.100
RUN ./configure \
--prefix="$HOME/ffmpeg_build" \
--bindir="$HOME/bin" \
--disable-shared \
--enable-nasm \
&& make && make install && make distclean

# Opus - a totally open, royalty-free, highly versatile audio codec.
WORKDIR ~/ffmpeg_sources
RUN git clone --depth 1 https://github.com/xiph/opus.git
WORKDIR opus
RUN autoreconf -fiv
RUN PKG_CONFIG_PATH="$HOME/ffmpeg_build/lib/pkgconfig" \
./configure \
--prefix="$HOME/ffmpeg_build" \
--disable-shared \
&& make && make install && make distclean

# OGG - for video, audio, and applications there's video/ogg, audio/ogg and
# application/ogg respectively.
WORKDIR ~/ffmpeg_sources
RUN curl -L -O http://downloads.xiph.org/releases/ogg/libogg-1.3.5.tar.gz
RUN tar xzvf libogg-1.3.5.tar.gz
WORKDIR libogg-1.3.5
RUN ./configure \
--prefix="$HOME/ffmpeg_build" \
--disable-shared \
&& make && make install && make distclean

# libvorbis - reference implementation provides both a standard encoder and
# decoder under a BSD license.
WORKDIR ~/ffmpeg_sources
RUN curl -L -O http://downloads.xiph.org/releases/vorbis/libvorbis-1.3.7.tar.gz
RUN tar xzvf libvorbis-1.3.7.tar.gz
WORKDIR libvorbis-1.3.7
RUN LDFLAGS="-L$HOME/ffmpeg_build/lib"
RUN CPPFLAGS="-I$HOME/ffmpeg_build/include"
RUN ./configure \
--prefix="$HOME/ffmpeg_build" \
--with-ogg="$HOME/ffmpeg_build" \
--disable-shared \
&& make && make install && make distclean

WORKDIR ~/ffmpeg_sources
RUN curl -L -O https://ffmpeg.org/releases/ffmpeg-6.1.tar.gz
RUN tar xzvf ffmpeg-6.1.tar.gz
WORKDIR ffmpeg-6.1
RUN PATH="$HOME/bin:$PATH" \
PKG_CONFIG_PATH="$HOME/ffmpeg_build/lib/pkgconfig" \
./configure \
--prefix="$HOME/ffmpeg_build" \
--extra-cflags="-I$HOME/ffmpeg_build/include" \
--extra-ldflags="-L$HOME/ffmpeg_build/lib" \
--bindir="$HOME/bin" \
--pkg-config-flags="--static" \
--enable-gpl \
--enable-nonfree \
--enable-libfreetype \
--enable-libmp3lame \
--enable-libopus \
--enable-libfdk-aac \
--enable-libvorbis \
--enable-libx264 \
# --enable-libx265 \
&& PATH="$HOME/bin:$PATH" make && make install && make distclean

# Make ffmpeg available
RUN cp $HOME/bin/ffmpeg /usr/bin/
RUN cp $HOME/bin/ffprobe /usr/bin/

# Test ffmpeg and ffprobe
COPY example.wav .
RUN ffprobe example.wav -v quiet -show_format -show_streams -of json
RUN ffmpeg -y -i example.wav -vn -codec:a libmp3lame -b:a 128k example.mp3
RUN ffmpeg -y -i example.wav -vn -strict -2 -codec:a libfdk_aac -b:a 96k example.m4a
RUN ffmpeg -y -i example.wav -vn -codec:a libvorbis example.ogg
RUN ffmpeg -y -i example.wav -filter_complex aformat=channel_layouts=mono,showwavespic=s=1200x400 -frames:v 1 example.png
RUN rm example.*

# Copy over binaries
COPY copy-binaries.sh .
RUN chmod +x copy-binaries.sh
RUN mkdir -p /ffmpeg/binaries
RUN ./copy-binaries.sh /usr/bin/ffmpeg /ffmpeg/binaries
RUN ./copy-binaries.sh /usr/bin/ffprobe /ffmpeg/binaries


# Copy function code and requirements
COPY requirements.txt google_auth.json lambda_function.py config.py ./

RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"
RUN chmod o+rx /root
RUN chmod o+rx "${LAMBDA_TASK_ROOT}"
RUN chmod 777 /root
RUN chmod 777 "${LAMBDA_TASK_ROOT}"
RUN chmod 777 "${HOME}"
# Set the CMD to your handler
CMD ["lambda_function.lambda_handler"]

