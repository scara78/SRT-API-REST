import re
import logging
import requests
from typing import Optional
import tempfile
import os

class FormatConverter:
    """Service for converting between SRT and VTT subtitle formats"""
    
    def __init__(self):
        pass
    
    def convert_content(self, content: str, from_format: str, to_format: str) -> str:
        """
        Convert subtitle content between formats
        
        Args:
            content: The subtitle content as string
            from_format: Source format ('srt' or 'vtt')
            to_format: Target format ('srt' or 'vtt')
        
        Returns:
            Converted subtitle content
        """
        if from_format == to_format:
            return content
        
        if from_format == 'srt' and to_format == 'vtt':
            return self._srt_to_vtt(content)
        elif from_format == 'vtt' and to_format == 'srt':
            return self._vtt_to_srt(content)
        else:
            raise ValueError(f"Unsupported conversion: {from_format} to {to_format}")
    
    def convert_subtitle_url(self, url: str, from_format: str, to_format: str) -> Optional[str]:
        """
        Download subtitle from URL and convert format
        
        Args:
            url: Direct download URL
            from_format: Source format
            to_format: Target format
        
        Returns:
            URL to converted content or None if conversion fails
        """
        try:
            # Download the original content
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Decode content
            content = response.content.decode('utf-8', errors='ignore')
            
            # Convert format
            converted_content = self.convert_content(content, from_format, to_format)
            
            # For now, return the converted content as a data URL
            # In a production environment, you might want to cache this on your server
            import base64
            encoded_content = base64.b64encode(converted_content.encode('utf-8')).decode('ascii')
            return f"data:text/plain;base64,{encoded_content}"
            
        except Exception as e:
            logging.error(f"URL conversion error: {e}")
            return None
    
    def _srt_to_vtt(self, srt_content: str) -> str:
        """Convert SRT format to VTT format"""
        try:
            lines = srt_content.strip().split('\n')
            vtt_lines = ['WEBVTT', '']
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # Skip empty lines
                if not line:
                    i += 1
                    continue
                
                # Check if this is a subtitle number (just digits)
                if line.isdigit():
                    i += 1
                    if i < len(lines):
                        # Next line should be timing
                        timing_line = lines[i].strip()
                        
                        # Convert SRT timing format to VTT
                        # SRT: 00:01:30,500 --> 00:01:35,000
                        # VTT: 00:01:30.500 --> 00:01:35.000
                        vtt_timing = timing_line.replace(',', '.')
                        vtt_lines.append(vtt_timing)
                        
                        i += 1
                        
                        # Collect subtitle text until next number or end
                        subtitle_text = []
                        while i < len(lines) and lines[i].strip() and not lines[i].strip().isdigit():
                            subtitle_text.append(lines[i].strip())
                            i += 1
                        
                        # Add subtitle text
                        vtt_lines.extend(subtitle_text)
                        vtt_lines.append('')  # Empty line after each subtitle
                    
                else:
                    i += 1
            
            return '\n'.join(vtt_lines)
            
        except Exception as e:
            logging.error(f"SRT to VTT conversion error: {e}")
            raise
    
    def _vtt_to_srt(self, vtt_content: str) -> str:
        """Convert VTT format to SRT format"""
        try:
            lines = vtt_content.strip().split('\n')
            srt_lines = []
            subtitle_number = 1
            
            i = 0
            # Skip WEBVTT header and any initial metadata
            while i < len(lines):
                line = lines[i].strip()
                if line.startswith('WEBVTT') or line.startswith('NOTE') or not line:
                    i += 1
                    continue
                
                # Look for timing lines
                if '-->' in line:
                    # Convert VTT timing to SRT timing
                    # VTT: 00:01:30.500 --> 00:01:35.000
                    # SRT: 00:01:30,500 --> 00:01:35,000
                    srt_timing = line.replace('.', ',')
                    
                    # Add subtitle number
                    srt_lines.append(str(subtitle_number))
                    srt_lines.append(srt_timing)
                    
                    i += 1
                    
                    # Collect subtitle text until next timing line or end
                    subtitle_text = []
                    while i < len(lines):
                        line = lines[i].strip()
                        if '-->' in line or not line:
                            break
                        if line:
                            subtitle_text.append(line)
                        i += 1
                    
                    # Add subtitle text
                    srt_lines.extend(subtitle_text)
                    srt_lines.append('')  # Empty line after each subtitle
                    
                    subtitle_number += 1
                else:
                    i += 1
            
            return '\n'.join(srt_lines)
            
        except Exception as e:
            logging.error(f"VTT to SRT conversion error: {e}")
            raise
    
    def validate_srt(self, content: str) -> bool:
        """Validate SRT format"""
        try:
            lines = content.strip().split('\n')
            has_timing = False
            
            for line in lines:
                if '-->' in line and ',' in line:
                    has_timing = True
                    break
            
            return has_timing
        except:
            return False
    
    def validate_vtt(self, content: str) -> bool:
        """Validate VTT format"""
        try:
            lines = content.strip().split('\n')
            has_webvtt = any(line.strip().startswith('WEBVTT') for line in lines[:3])
            has_timing = any('-->' in line and '.' in line for line in lines)
            
            return has_webvtt and has_timing
        except:
            return False
