import reapy
from reapy import reascript_api as RPR
from reapy.core import ReapyObject
from reapy.tools import depends_on_sws


class Send(ReapyObject):
    """Track send.

    Attributes
    ----------
    index : int
        position on the track
    is_muted : bool
    is_phase_flipped : bool
    track_id : str
    type : str
        can be 'send', 'hardware' or 'receive'
    """

    _class_name = "Send"

    def __init__(self, track=None, index=0, track_id=None, type="send"):
        if track_id is None:
            message = "One of `track` or `track_id` must be specified."
            assert track is not None, message
            track_id = track.id
        self.index = index
        self.track_id = track_id
        self.type = type

    def _get_int_type(self):
        types = {
            "hardware": 1,
            "send": 0,
            "receive": -1,
        }
        int_type = types[self.type]
        return int_type

    @property
    def _kwargs(self):
        return {
            "index": self.index,
            "track_id": self.track_id,
            "type": self.type
        }

    def delete(self):
        """
        Delete send.
        """
        RPR.RemoveTrackSend(self.track_id, self._get_int_type(), self.index)

    @property
    def dest_track(self):
        """
        Destination track.

        :type: Track
        """
        pointer = self.get_info('P_DESTTRACK')
        track_id = reapy.Track._get_id_from_pointer(pointer)
        return reapy.Track(track_id)

    @reapy.inside_reaper()
    def flip_phase(self):
        """
        Toggle whether phase is flipped.
        """
        self.is_phase_flipped = not self.is_phase_flipped

    def get_info(self, param_name):
        """Get raw info from GetTrackSendInfo_Value.

        Parameters
        ----------
        param_name : str
            B_MUTE : bool *
            B_PHASE : bool *, true to flip phase
            B_MONO : bool *
            D_VOL : double *, 1.0 = +0dB etc
            D_PAN : double *, -1..+1
            D_PANLAW : double *,1.0=+0.0db, 0.5=-6dB, -1.0 = projdef etc
            I_SENDMODE : int *, 0=post-fader, 1=pre-fx, 2=post-fx (deprecated),
                                3=post-fx
            I_AUTOMODE : int * : automation mode (-1=use track automode,
                                0=trim/off, 1=read, 2=touch, 3=write, 4=latch)
            I_SRCCHAN : int *, index,&1024=mono, -1 for none
            I_DSTCHAN : int *, index, &1024=mono, otherwise stereo pair,
                                hwout:&512=rearoute
            I_MIDIFLAGS : int *, low 5 bits=source channel 0=all, 1-16,
                                next 5 bits=dest channel, 0=orig,
                                1-16=chan
            P_DESTTRACK : read only, returns MediaTrack *,
                                destination track,
                                only applies for sends/recvs
            P_SRCTRACK : read only, returns MediaTrack *,
                                source track, only applies for sends/recvs
            P_ENV:<envchunkname : read only, returns TrackEnvelope *.
                                Call with :<VOLENV, :<PANENV, etc appended.


        Returns
        -------
        Union[bool, track id(str)]
        """
        value = RPR.GetTrackSendInfo_Value(
            self.track_id, self._get_int_type(), self.index, param_name
        )
        return value

    @depends_on_sws
    def get_sws_info(self, param_name):
        """Raw value from BR_GetSetTrackSendInfo.

        Parameters
        ----------
        param_name : str
            B_MUTE : send mute state (1.0 if muted, otherwise 0.0)
            B_PHASE : send phase state (1.0 if phase is inverted, otherwise 0.0)
            B_MONO : send mono state (1.0 if send is set to mono, otherwise 0.0)
            D_VOL : send volume (1.0=+0dB etc...)
            D_PAN : send pan (-1.0=100%L, 0=center, 1.0=100%R)
            D_PANLAW : send pan law (1.0=+0.0db, 0.5=-6dB,
                        -1.0=project default etc...)
            I_SENDMODE : send mode (0=post-fader, 1=pre-fx, 2=post-fx(deprecated),
                        3=post-fx)
            I_SRCCHAN : audio source starting channel index or -1 if audio send
                        is disabled (&1024=mono...note that in that case, when
                        reading index, you should do (index XOR 1024) to get
                        starting channel index)
            I_DSTCHAN : audio destination starting channel index (&1024=mono
                        (and in case of hardware output &512=rearoute)...
                        note that in that case, when reading index, you should do
                        (index XOR (1024 OR 512)) to get starting channel index)
            I_MIDI_SRCCHAN : source MIDI channel, -1 if MIDI send is disabled
                            (0=all, 1-16)
            I_MIDI_DSTCHAN : destination MIDI channel, -1 if MIDI send is disabled
                            (0=original, 1-16)
            I_MIDI_SRCBUS : source MIDI bus, -1 if MIDI send is disabled
                            (0=all, otherwise bus index)
            I_MIDI_DSTBUS : receive MIDI bus, -1 if MIDI send is disabled
                            (0=all, otherwise bus index)
            I_MIDI_LINK_VOLPAN : link volume/pan controls to MIDI

        Returns
        -------
        float
        """
        value = RPR.BR_GetSetTrackSendInfo(
            self.track_id, self._get_int_type(), self.index, param_name, False,
            0.0
        )
        return value

    @property
    def is_mono(self):
        """
        Whether send is mono or stereo.

        :type: bool
        """
        is_mono = bool(self.get_info("B_MONO"))
        return is_mono

    @is_mono.setter
    def is_mono(self, mono):
        self.set_info("B_MONO", mono)

    @property
    def is_muted(self):
        """
        Whether send is muted.

        :type: bool
        """
        is_muted = bool(self.get_info("B_MUTE"))
        return is_muted

    @is_muted.setter
    def is_muted(self, is_muted):
        """
        Mute or unmute send.

        Parameters
        ----------
        is_muted : bool
            Whether to mute or unmute send.
        """
        self.set_info("B_MUTE", is_muted)

    @property
    def is_phase_flipped(self):
        """
        Whether send phase is flipped (i.e. signal multiplied by -1).

        :type: bool
        """
        is_phase_flipped = bool(self.get_info("B_PHASE"))
        return is_phase_flipped

    @is_phase_flipped.setter
    def is_phase_flipped(self, flipped):
        self.set_info("B_PHASE", flipped)

    @property
    def _midi_flags_unpacked(self):
        flags = int(self.get_info('I_MIDIFLAGS'))
        if flags == 0b1111111100000000011111:
            return ((-1, -1), (-1, -1))
        ch_flags = flags % 0b10000000000
        bus_flags = flags >> 14
        # bus
        src_bus = bus_flags % 0b100000
        dst_bus = bus_flags >> 8
        # channel
        src_ch = ch_flags % 0b100000
        dst_ch = ch_flags >> 5

        return ((src_bus, src_ch), (dst_bus, dst_ch))

    @_midi_flags_unpacked.setter
    def _midi_flags_unpacked(self, in_tuple):
        src_bus, src_ch, dst_bus, dst_ch = (*in_tuple[0], *in_tuple[1])
        dst_ch <<= 5
        src_bus <<= 14
        dst_bus <<= 22
        flags = src_bus | src_ch | dst_bus | dst_ch
        if flags == -1:
            flags = 0b1111111100000000011111
        self.set_info('I_MIDIFLAGS', flags)

    @property
    def midi_source(self):
        """
        Send MIDI properties on the send track.

        Returns
        -------
        Tuple[int bus, int channel]
        """
        return tuple(self._midi_flags_unpacked[0])

    @midi_source.setter
    @reapy.inside_reaper()
    def midi_source(self, source):
        dest = self._midi_flags_unpacked[1]
        self._midi_flags_unpacked = (source, dest)

    @property
    def midi_dest(self):
        """
        Send MIDI properties on the receive track.

        Returns
        -------
        Tuple[int bus, int channel]
        """
        return tuple(self._midi_flags_unpacked[1])

    @midi_dest.setter
    @reapy.inside_reaper()
    def midi_dest(self, dest):
        source = self._midi_flags_unpacked[0]
        self._midi_flags_unpacked = (source, dest)

    def mute(self):
        """
        Mute send.
        """
        self.is_muted = True

    @property
    def pan(self):
        """
        Send pan (from -1=left to 1=right).

        :type: float
        """
        pan = self.get_info("D_PAN")
        return pan

    @pan.setter
    def pan(self, pan):
        """
        Set send pan.

        Parameters
        ----------
        pan : float
            New pan between -1 (left) and 1 (right).
        """
        self.set_info("D_PAN", pan)

    def send_to_mono_output(self, ch):
        """
        Send to mono output.

        Parameters
        ----------
        ch : int
            Channel index. 0 is Output1
        """
        self.set_info("I_DSTCHAN", ch+1024)

    def send_to_stereo_output(self, ch):
        """
        Send to stereo output.

        Parameters
        ----------
        ch : int
            Channel index. 0 is Output1 & Outpu2
        """
        self.set_info("I_DSTCHAN", ch)

    def set_info(self, param_name, value):
        """
        Set send info.

        Parameters
        ----------
        param_name : str
            Parameter name.
            B_MUTE : bool *
            B_PHASE : bool * : true to flip phase
            B_MONO : bool *
            D_VOL : double * : 1.0 = +0dB etc
            D_PAN : double * : -1..+1
            D_PANLAW : double * : 1.0=+0.0db, 0.5=-6dB, -1.0 = projdef etc
            I_SENDMODE : int * : 0=post-fader, 1=pre-fx, 2=post-fx (deprecated), 3=post-fx
            I_AUTOMODE : int * : automation mode (-1=use track automode, 0=trim/off, 1=read, 2=touch, 3=write, 4=latch)
            I_SRCCHAN : int * : index,&1024=mono, -1 for none
            I_DSTCHAN : int * : index, &1024=mono, otherwise stereo pair, hwout:&512=rearoute
            I_MIDIFLAGS : int * : low 5 bits=source channel 0=all, 1-16, next 5 bits=dest channel, 0=orig, 1-16=chan
        value : bool, int or float
            New value.
        """
        RPR.SetTrackSendInfo_Value(
            self.track_id, self._get_int_type(), self.index, param_name, value
        )

    @depends_on_sws
    def set_sws_info(self, param_name, value):
        RPR.BR_GetSetTrackSendInfo(
            self.track_id, self._get_int_type(), self.index, param_name, True,
            value
        )

    @property
    def source_track(self):
        """
        Source track.

        :type: Track
        """
        pointer = self.get_info('P_SRCTRACK')
        track_id = reapy.Track._get_id_from_pointer(pointer)
        return reapy.Track(track_id)

    def unmute(self):
        """
        Unmute send.
        """
        self.is_muted = False

    @property
    def volume(self):
        """
        Send volume.

        :type: float
        """
        volume = self.get_info("D_VOL")
        return volume

    @volume.setter
    def volume(self, volume):
        self.set_info("D_VOL", volume)

